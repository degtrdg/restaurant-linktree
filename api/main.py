from chatgpt import complete
import re
from diff_match_patch import diff_match_patch

dmp = diff_match_patch()


def pretty_diff(paragraph, revised_paragraph):
    dmp = diff_match_patch()
    diffs = dmp.diff_main(paragraph, revised_paragraph)
    dmp.diff_cleanupSemantic(diffs)  # Optionally clean up semantic clutter

    # Using ANSI codes to color the diffs
    diff_display = []
    for op, data in diffs:
        if op == dmp.DIFF_INSERT:
            # Green for inserts
            diff_display.append('\033[32m' + data + '\033[0m')
        elif op == dmp.DIFF_DELETE:
            diff_display.append('\033[31m' + data +
                                '\033[0m')  # Red for deletes
        elif op == dmp.DIFF_EQUAL:
            diff_display.append(data)

    return ''.join(diff_display)


def pretty_diff_to_html(paragraph, revised_paragraph):
    dmp = diff_match_patch()
    diffs = dmp.diff_main(paragraph, revised_paragraph)
    dmp.diff_cleanupSemantic(diffs)  # Optionally clean up semantic clutter

    # Convert diffs to HTML with Tailwind CSS classes
    diff_display = []
    for op, data in diffs:
        if op == dmp.DIFF_INSERT:
            # Green for inserts
            diff_display.append(
                '<span class="text-green-500">' + data + '</span>')
        elif op == dmp.DIFF_DELETE:
            diff_display.append('<span class="text-red-500">' +
                                data + '</span>')  # Red for deletes
        elif op == dmp.DIFF_EQUAL:
            diff_display.append(data)

    return ''.join(diff_display)


prompt = '''
We have made a research proposal and have been given a weakness of the proposal by a reviewer. We're only given a single paragraph of the proposal to work on. We'll be revising the paragraph to address the weakness. Maintain the exact style and wording unless the change addresses the weakness.

Paragraph:
```md
{paragraphs}
```

Weakness:
```md
{weakness}
```

Output the revised paragraph. Your revision based on the weakness should be in a md codeblock like you've seen above.
'''.strip()

prompt_filter = '''
We have made a research proposal and have been given a weakness of the proposal by a reviewer. We're only given a single paragraph of the proposal to work on. We'll be looking at the proposal one paragraph at a time and see if this is the specific paragraph that needs to be revised in order to address the weakness as opposed to somewhere else in the proposal.

Paragraph:
```md
{paragraphs}
```

Weakness:
```md
{weakness}
```

Think step by step if the paragraph needs to be changed or not with respect to the given weakness. The last line of your response should be of the following format: 'ANSWER: $YESORNO' (without quotes) where YESORNO is one of Yes or No.
'''.strip()

sysprompt = '''
You are a PI responding to a reviewer's comment on a research proposal. The reviewer has pointed out a weakness in the proposal. You are looking at the proposal a couple of paragraphs at a time and seeing if the paragraphs need to be revised to address the weakness. If the paragraphs don't need to be changed, do not give an edit.
'''.strip()


# Read the text content from the files
with open('api/text.txt', 'r') as file:
    text_content = file.read()

with open('api/weaknes.txt', 'r') as file:
    weakness_content = file.read()

# Split the text content into paragraphs
paragraphs = text_content.split('\n\n')
# Split the weakness content into individual weaknesses
weaknesses = weakness_content.split('\n\n')

ANSWER_PATTERN = r"(?i)ANSWER\s*:\s*(Yes|No)"

# markdown codeblock pattern
MARKDOWN_PATTERN = r"```md(.*?)```"

# Iterate through the paragraphs and weaknesses and process them
for weakness in weaknesses:
    for paragraph in paragraphs:
        # Prepare the prompt with the current paragraph and weakness
        filter = prompt_filter.format(paragraphs=paragraph, weakness=weakness)
        # Call the complete function from chatgpt.py to get the revision
        filter_answer = complete(messages=[{"role": "system", "content": sysprompt},
                                           {"role": "user", "content": filter}], model="gpt-3.5-turbo")
        # Check if the user's response contains the answer pattern
        match = re.search(ANSWER_PATTERN, filter_answer)
        if match:
            user_answer = match.group(1)
            if user_answer.lower() == 'no':
                continue
            # try it again with gpt-4-turbo-preview
            filter_answer = complete(messages=[{"role": "system", "content": sysprompt},
                                               {"role": "user", "content": filter}])
            match = re.search(ANSWER_PATTERN, filter_answer)
            if match:
                user_answer = match.group(1)
                if user_answer.lower() == 'no':
                    continue
        else:
            # try one more time otherwise print error and move on
            filter_answer = complete(messages=[{"role": "system", "content": sysprompt},
                                               {"role": "user", "content": prompt_filter}])
            match = re.search(ANSWER_PATTERN, filter_answer)
            if match:
                user_answer = match.group(1)
                if user_answer.lower() == 'no':
                    continue
            else:
                print(
                    "Error: Could not extract the answer from the user's response. Moving to the next paragraph.")
                continue

        # Prepare the prompt with the current paragraph and weakness
        current_prompt = prompt.format(paragraphs=paragraph, weakness=weakness)

        # Call the complete function from chatgpt.py to get the revision
        revision = complete(messages=[{"role": "system", "content": sysprompt},
                                      {"role": "user", "content": current_prompt}])

        # Check if the revision is in markdown codeblock format
        match = re.search(MARKDOWN_PATTERN, revision, re.DOTALL)
        if match:
            revision = match.group(1).strip()
        else:
            # try one more time otherwise print error and move on
            revision = complete(messages=[{"role": "system", "content": sysprompt},
                                          {"role": "user", "content": current_prompt}])
            match = re.search(MARKDOWN_PATTERN, revision)
            if match:
                revision = match.group(1).strip()
            else:
                print(
                    "Error: Could not extract the revision from the model's response. Moving to the next paragraph.")
                # print more info to help debug
                print(f'current_prompt: {current_prompt}')
                print(f'revision: {revision}')
                continue

        # Output the revision
        print('revision complete!')
        print('---')
        print(revision)
        print('---')
        print('\n')
        print('\n')
        # print diff of revision and original paragraph
        print('diff complete!')
        print('---')
        print(pretty_diff(paragraph, revision))
        print('---')
        print('\n')
