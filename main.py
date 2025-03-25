from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import httpx
import json
from query_openai import QueryOpenAi
import os
import markdown2
import pdfkit
from xhtml2pdf import pisa

# Initialize FastAPI app
app = FastAPI()

# Mount static directory for CSS, JS, and images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Load environment variables
load_dotenv()

@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    '''
        default application endpoint 
        directly renders the index.html template
    '''
    return templates.TemplateResponse("index.html", {"request": request, "username": "Guest"})

@app.get("/home", response_class=HTMLResponse)
async def auth_redirect(request: Request):
    '''
        home endpoint 
        directly renders the index.html template
    '''
    return templates.TemplateResponse("index.html", {"request": request, "username": "Dr Gupta Clinic"})

# Streaming endpoint
@app.get("/stream")
async def stream(
    request: Request,
    search_query: str = Query(...),
    topNDocuments: int = Query(5),
    sessionID: str = Query(...),
):
    print(
        f"search_query is {search_query}, topNDocuments is {topNDocuments}, sessionID is {sessionID}"
    )
    # Write sessionID to a file
    with open("sessionID.txt", "w") as f:
        f.write(sessionID)

    query_rag = QueryOpenAi()
    

    def event_generator():
        response_chunks = []
        for content in query_rag.query_openai(search_query):
            json_content = json.dumps({'type': 'response', 'data': content})
            # Make the response SSE compliant
            sse_content = f"data: {json_content}\n\n"
            print(sse_content)  # Debugging: Print the content to the console
            yield sse_content

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/save_meal_plan")
async def save_meal_plan(request: Request):
    """
    Endpoint to save the meal plan as both Markdown and PDF files.
    """
    data = await request.json()
    meal_plan = data.get("meal_plan")
    patient_name = data.get("name")
    date_str = datetime.now().strftime("%Y-%m-%d")

    if not meal_plan or not patient_name:
        raise HTTPException(status_code=400, detail="Meal plan or patient name is missing.")

    # Ensure the saved_recipes folder exists
    os.makedirs("saved_recipes", exist_ok=True)

    # Create the file names
    file_name_md = f"{patient_name}_{date_str}.md"
    file_name_pdf = f"{patient_name}_{date_str}.pdf"
    file_path_md = os.path.join("saved_recipes", file_name_md)
    file_path_pdf = os.path.join("saved_recipes", file_name_pdf)

    # Save the meal plan to the Markdown file
    with open(file_path_md, "w") as f:
        f.write(meal_plan)

    # Convert Markdown to HTML
    html_content = markdown2.markdown(meal_plan)

    # Convert HTML to PDF using xhtml2pdf
    with open(file_path_pdf, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
        if pisa_status.err:
            raise HTTPException(status_code=500, detail="Error generating PDF.")

    return {"message": f"Meal plan saved as {file_name_md} and {file_name_pdf}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)