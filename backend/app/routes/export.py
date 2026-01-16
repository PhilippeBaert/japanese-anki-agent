"""Export endpoint for downloading CSV files."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import io
import zipfile

from ..models import ExportRequest, ExportWithPriorityRequest
from ..config import load_config
from ..services.csv_export import generate_csv, generate_csv_with_priority, get_csv_filename
from ..auth import verify_api_key

router = APIRouter()


@router.post("/export", dependencies=[Depends(verify_api_key)])
async def export_csv(request: ExportRequest) -> StreamingResponse:
    """
    Export generated cards to a CSV file.

    Args:
        request: ExportRequest containing cards and filename

    Returns:
        CSV file download response
    """
    config = load_config()

    if not request.cards:
        raise HTTPException(status_code=400, detail="No cards to export")

    try:
        # Generate CSV content
        csv_content = generate_csv(
            cards=request.cards,
            config=config,
            source=request.source,
        )

        # Create filename
        filename = get_csv_filename(request.filename)

        # Return as streaming response for download
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8')),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/export-priority", dependencies=[Depends(verify_api_key)])
async def export_csv_with_priority(request: ExportWithPriorityRequest) -> StreamingResponse:
    """
    Export cards split by core/extra priority.

    Returns:
        - Single CSV if only one category has cards
        - ZIP file with both CSVs if both categories have cards
    """
    config = load_config()

    has_core = len(request.core_cards) > 0
    has_extra = len(request.extra_cards) > 0

    if not has_core and not has_extra:
        raise HTTPException(status_code=400, detail="No cards to export")

    try:
        # Sanitize base filename
        base_filename = request.filename.replace('.csv', '').replace('.zip', '').strip() or 'anki_cards'
        safe_base = ''.join(c for c in base_filename if c.isalnum() or c in ('_', '-', ' '))
        safe_base = safe_base.strip() or 'anki_cards'

        # Case 1: Only core cards - return single CSV
        if has_core and not has_extra:
            csv_content = generate_csv_with_priority(
                cards=request.core_cards,
                config=config,
                source=request.source,
                is_core=True,
            )
            filename = f"{safe_base}_core.csv"
            return StreamingResponse(
                io.BytesIO(csv_content.encode('utf-8')),
                media_type='text/csv',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'},
            )

        # Case 2: Only extra cards - return single CSV
        if has_extra and not has_core:
            csv_content = generate_csv_with_priority(
                cards=request.extra_cards,
                config=config,
                source=request.source,
                is_core=False,
            )
            filename = f"{safe_base}_extra.csv"
            return StreamingResponse(
                io.BytesIO(csv_content.encode('utf-8')),
                media_type='text/csv',
                headers={'Content-Disposition': f'attachment; filename="{filename}"'},
            )

        # Case 3: Both core and extra cards - return ZIP
        core_csv = generate_csv_with_priority(
            cards=request.core_cards,
            config=config,
            source=request.source,
            is_core=True,
        )
        extra_csv = generate_csv_with_priority(
            cards=request.extra_cards,
            config=config,
            source=request.source,
            is_core=False,
        )

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(f"{safe_base}_core.csv", core_csv)
            zip_file.writestr(f"{safe_base}_extra.csv", extra_csv)

        zip_buffer.seek(0)
        zip_filename = f"{safe_base}.zip"

        return StreamingResponse(
            zip_buffer,
            media_type='application/zip',
            headers={'Content-Disposition': f'attachment; filename="{zip_filename}"'},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
