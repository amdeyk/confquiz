from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from database import get_db
from auth import get_current_admin
from models import User, Session, Deck, Slide, SlideMapping
from schemas import DeckResponse, SlideMappingCreate
from services.media_service import media_service

router = APIRouter()


@router.post("/sessions/{session_id}/decks", response_model=DeckResponse)
async def upload_deck(
    session_id: int,
    deck_type: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Upload PPT deck and convert to images"""
    # Verify session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate deck type
    if deck_type not in ["question", "answer"]:
        raise HTTPException(status_code=400, detail="Invalid deck type")

    # Validate file type
    if not file.filename.endswith(('.ppt', '.pptx')):
        raise HTTPException(status_code=400, detail="Only PPT/PPTX files allowed")

    # Save PPT file
    ppt_path = await media_service.save_ppt(file)

    # Create deck record
    deck = Deck(
        session_id=session_id,
        deck_type=deck_type,
        ppt_path=ppt_path,
        native_required=False
    )
    db.add(deck)
    await db.flush()

    # Convert to images
    try:
        slides_data = media_service.convert_ppt_to_images(ppt_path, deck.id)

        # Create slide records
        for slide_data in slides_data:
            slide = Slide(
                deck_id=deck.id,
                slide_index=slide_data["slide_index"],
                png_path=slide_data["png_path"],
                thumb_path=slide_data["thumb_path"]
            )
            db.add(slide)

        await db.commit()

        # Refresh deck with eager-loaded slides to avoid lazy loading issues
        result = await db.execute(
            select(Deck)
            .where(Deck.id == deck.id)
            .options(selectinload(Deck.slides))
        )
        deck = result.scalar_one()

        return deck

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing PPT: {str(e)}")


@router.get("/sessions/{session_id}/decks", response_model=List[DeckResponse])
async def list_decks(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all decks in session"""
    # Use eager loading to avoid lazy loading issues in async context
    result = await db.execute(
        select(Deck)
        .where(Deck.session_id == session_id)
        .options(selectinload(Deck.slides))
    )
    decks = result.scalars().all()

    return decks


@router.post("/sessions/{session_id}/mappings")
async def create_slide_mappings(
    session_id: int,
    mappings: List[SlideMappingCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Create question->answer slide mappings"""
    # Verify session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete existing mappings (if updating)
    # Create new mappings
    for mapping_data in mappings:
        # Verify slides exist
        result = await db.execute(
            select(Slide).where(Slide.id == mapping_data.question_slide_id)
        )
        question_slide = result.scalar_one_or_none()

        result = await db.execute(
            select(Slide).where(Slide.id == mapping_data.answer_slide_id)
        )
        answer_slide = result.scalar_one_or_none()

        if not question_slide or not answer_slide:
            raise HTTPException(status_code=400, detail="Invalid slide IDs")

        # Check if mapping exists
        result = await db.execute(
            select(SlideMapping)
            .where(SlideMapping.question_slide_id == mapping_data.question_slide_id)
        )
        existing_mapping = result.scalar_one_or_none()

        if existing_mapping:
            # Update existing
            existing_mapping.answer_slide_id = mapping_data.answer_slide_id
            existing_mapping.answer_timer_override_ms = mapping_data.answer_timer_override_ms
        else:
            # Create new
            mapping = SlideMapping(
                question_slide_id=mapping_data.question_slide_id,
                answer_slide_id=mapping_data.answer_slide_id,
                answer_timer_override_ms=mapping_data.answer_timer_override_ms
            )
            db.add(mapping)

    await db.commit()

    return {"message": f"Created/updated {len(mappings)} slide mappings"}


@router.get("/sessions/{session_id}/mappings")
async def get_slide_mappings(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all slide mappings for a session"""
    # Get all decks for this session
    result = await db.execute(
        select(Deck).where(Deck.session_id == session_id)
    )
    decks = result.scalars().all()

    deck_ids = [deck.id for deck in decks]

    # Get all mappings for slides in these decks
    result = await db.execute(
        select(SlideMapping, Slide)
        .join(Slide, SlideMapping.question_slide_id == Slide.id)
        .where(Slide.deck_id.in_(deck_ids))
    )

    mappings = []
    for mapping, slide in result:
        mappings.append({
            "question_slide_id": mapping.question_slide_id,
            "answer_slide_id": mapping.answer_slide_id,
            "answer_timer_override_ms": mapping.answer_timer_override_ms
        })

    return mappings
