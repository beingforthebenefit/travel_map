import asyncio
import uuid
from dataclasses import dataclass, field

from app.renderer.pipeline import generate_map, generate_preview
from app.renderer.styles import get_style, get_available_styles, STYLES
from app.config import settings


@dataclass
class RenderJob:
    job_id: str
    trip_id: str
    status: str = "pending"  # pending | rendering | done | error
    progress: float = 0.0
    styles_complete: list[str] = field(default_factory=list)
    error: str | None = None


# In-memory job store (single-user, self-hosted)
_jobs: dict[str, RenderJob] = {}
# Map trip_id -> latest job_id
_trip_jobs: dict[str, str] = {}


def get_job(trip_id: str) -> RenderJob | None:
    job_id = _trip_jobs.get(trip_id)
    if job_id:
        return _jobs.get(job_id)
    return None


async def start_render(
    trip: dict,
    stops: list[dict],
    style: str | None = None,
    all_styles: bool = False,
) -> str:
    """Start a render job. Returns job_id."""
    job_id = str(uuid.uuid4())
    job = RenderJob(job_id=job_id, trip_id=trip["id"])
    _jobs[job_id] = job
    _trip_jobs[trip["id"]] = job_id

    # Determine which styles to render
    api_key = settings.stadia_api_key
    if all_styles:
        styles_to_render = [s.name for s in get_available_styles(bool(api_key))]
    elif style:
        styles_to_render = [style]
    else:
        styles_to_render = [trip.get("style", "watercolor")]

    # Validate style availability
    for s in styles_to_render:
        st = get_style(s)
        if st.requires_api_key and not api_key:
            # Fall back to positron if no API key
            styles_to_render = [
                "positron" if get_style(x).requires_api_key else x
                for x in styles_to_render
            ]
            break

    asyncio.create_task(_run_render(job, trip, stops, styles_to_render, api_key))
    return job_id


async def _run_render(
    job: RenderJob,
    trip: dict,
    stops: list[dict],
    styles: list[str],
    api_key: str,
):
    job.status = "rendering"
    total = len(styles)

    try:
        for i, style_name in enumerate(styles):
            def progress_cb(pct: float):
                job.progress = (i + pct) / total

            await generate_map(
                trip=trip,
                stops=stops,
                style_name=style_name,
                api_key=api_key,
                data_dir=settings.data_dir,
                progress_callback=progress_cb,
            )
            job.styles_complete.append(style_name)

        job.status = "done"
        job.progress = 1.0
    except Exception as e:
        job.status = "error"
        job.error = str(e)
