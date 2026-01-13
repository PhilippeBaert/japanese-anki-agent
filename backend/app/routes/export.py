"""Export endpoint for downloading CSV files."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import io

from ..models import ExportRequest
from ..config import load_config
from ..services.csv_export import generate_csv, get_csv_filename
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
