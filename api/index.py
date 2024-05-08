from fastapi import FastAPI
from pydantic import BaseModel
from diff_match_patch import diff_match_patch
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from .prompts import prompt, prompt_filter, sysprompt, ANSWER_PATTERN, MARKDOWN_PATTERN
from .chatgpt import complete
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestBody(BaseModel):
    paragraph: str
    weakness: str


class ResponseBody(BaseModel):
    original: str
    revised: str
    diff_html: str


app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json")


dmp = diff_match_patch()


def pretty_diff_to_html(original: str, revised: str) -> str:
    diffs = dmp.diff_main(original, revised)
    dmp.diff_cleanupSemantic(diffs)  # Clean up semantic clutter
    diff_html = []
    for op, data in diffs:
        if op == dmp.DIFF_INSERT:
            diff_html.append(f'<span class="text-green-500">{data}</span>')
        elif op == dmp.DIFF_DELETE:
            diff_html.append(f'<span class="text-red-500">{data}</span>')
        elif op == dmp.DIFF_EQUAL:
            diff_html.append(data)
    return ''.join(diff_html)


@app.post("/api/process", response_model=ResponseBody)
async def process_paragraph(request: RequestBody) -> ResponseBody:
    paragraph = request.paragraph
    weakness = request.weakness

    # Function to call the complete function and extract the answer
    def get_revision(prompt_text, model_version):
        response = complete(messages=[{"role": "system", "content": sysprompt},
                                      {"role": "user", "content": prompt_text}], model=model_version)
        return response

    # Check if the paragraph needs to be revised
    filter_prompt = prompt_filter.format(
        paragraphs=paragraph, weakness=weakness)
    filter_answer = get_revision(filter_prompt, "gpt-3.5-turbo")
    match = re.search(ANSWER_PATTERN, filter_answer)
    if match:
        user_answer = match.group(1)
        if user_answer.lower() == 'no':
            # If still no match or answer is 'no', return the original paragraph
            return ResponseBody(
                original=paragraph,
                revised=paragraph,
                diff_html=pretty_diff_to_html(paragraph, paragraph)
            )
        filter_answer = get_revision(filter_prompt, "gpt-4-turbo-preview")
        match = re.search(ANSWER_PATTERN, filter_answer)
        if match:
            user_answer = match.group(1)
            if user_answer.lower() == 'no':
                return ResponseBody(
                    original=paragraph,
                    revised=paragraph,
                    diff_html=pretty_diff_to_html(paragraph, paragraph)
                )
    else:
        # try one more time otherwise print error and move on
        filter_answer = get_revision(filter_prompt, "gpt-4-turbo-preview")
        match = re.search(ANSWER_PATTERN, filter_answer)
        if match:
            user_answer = match.group(1)
            if user_answer.lower() == 'no':
                return ResponseBody(
                    original=paragraph,
                    revised=paragraph,
                    diff_html=pretty_diff_to_html(paragraph, paragraph)
                )
        else:
            print(
                'Error: Could not extract the answer from the user\'s response. Moving to the next paragraph.')
            return ResponseBody(
                original=paragraph,
                revised=paragraph,
                diff_html=pretty_diff_to_html(paragraph, paragraph)
            )

    # Get the revision for the paragraph
    current_prompt = prompt.format(paragraphs=paragraph, weakness=weakness)
    revision = get_revision(current_prompt, "gpt-4-turbo-preview")
    match = re.search(MARKDOWN_PATTERN, revision, re.DOTALL)
    if match:
        revision = match.group(1).strip()
    else:
        # If no match, try one more time
        revision = get_revision(current_prompt, "gpt-4-turbo-preview")
        match = re.search(MARKDOWN_PATTERN, revision)
        if match:
            revision = match.group(1).strip()
        else:
            # If still no match, log error and return the original paragraph
            print("Error: Could not extract the revision from the model's response.")
            print(f'current_prompt: {current_prompt}')
            print(f'revision: {revision}')
            return ResponseBody(
                original=paragraph,
                revised=paragraph,
                diff_html=pretty_diff_to_html(paragraph, paragraph)
            )

    # Generate the diff HTML
    diff_html = pretty_diff_to_html(paragraph, revision)

    return ResponseBody(
        original=paragraph,
        revised=revision,
        diff_html=diff_html
    )
