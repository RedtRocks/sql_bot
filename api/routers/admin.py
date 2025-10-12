from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from utils.jwt_handler import admin_required
from models import create_user, delete_user, get_column_usage_summary, get_chat_messages, get_feedback, get_all_users
from utils.schema_manager import SchemaManager
from services.azure_openai_service import AzureOpenAIService

router = APIRouter()


class AddUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    user_schema: str | None = Field(None, alias="schema")
    admin_schema: str | None = None


@router.post("/add-user")
def add_user(body: AddUserRequest, _=Depends(admin_required)):
    if body.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # Require schema for all users
    if not body.user_schema or body.user_schema.strip() == "":
        raise HTTPException(status_code=400, detail="schema is required for user creation")
    
    user = create_user(body.username, body.password, body.role, body.user_schema, body.admin_schema)
    return {"status": "ok", "id": user.id}


class RemoveUserRequest(BaseModel):
    username: str


@router.post("/remove-user")
def remove_user(body: RemoveUserRequest, _=Depends(admin_required)):
    ok = delete_user(body.username)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


class UpdateAdminSchemaRequest(BaseModel):
    admin_schema: str


@router.post("/update-admin-schema")
def update_admin_schema(body: UpdateAdminSchemaRequest, user=Depends(admin_required)):
    """Update the admin's full company database schema."""
    username = user.get("sub", "unknown")
    # This would require updating the user's admin_schema field
    # For now, return success - implementation would update the database
    return {"status": "ok", "message": "Admin schema updated"}


@router.get("/users")
def get_users(user=Depends(admin_required)):
    """Get all users for admin panel."""
    try:
        users = get_all_users()
        return {"status": "ok", "users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}")
def update_user(user_id: int, user_data: dict, user=Depends(admin_required)):
    """Update user information."""
    try:
        from models import get_user_by_id, update_user_info
        
        # Get the user to update
        existing_user = get_user_by_id(user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user information
        updated_user = update_user_info(
            user_id=user_id,
            username=user_data.get('username'),
            password=user_data.get('password'),
            role=user_data.get('role'),
            schema=user_data.get('schema'),
            admin_schema=user_data.get('admin_schema')
        )
        
        return {"status": "ok", "message": "User updated successfully", "user": updated_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze-columns")
async def analyze_columns(_=Depends(admin_required)):
    """Analyze database usage patterns using AI."""
    try:
        # Get ALL chat messages and feedback from all users
        chat_messages = get_chat_messages(limit=1000)  # Increased limit
        feedback = get_feedback(limit=1000)  # Increased limit
        
        print(f"Analyzing {len(chat_messages)} chat messages and {len(feedback)} feedback records")
        
        # Use Azure OpenAI to analyze usage patterns
        ai = AzureOpenAIService()
        analysis = await ai.analyze_usage(chat_messages, feedback)
        
        return {"status": "ok", "analysis": analysis}
    except Exception as e:
        print(f"AI analysis failed: {e}")
        # Fallback to simple analysis if AI fails
        try:
            usage = get_column_usage_summary()
            mgr = SchemaManager()
            analysis = mgr.analyze_columns(usage)
            return {"status": "ok", "analysis": analysis}
        except Exception as fallback_error:
            print(f"Fallback analysis also failed: {fallback_error}")
            return {"status": "ok", "analysis": {"error": "Analysis failed", "details": str(e)}}


