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

ANSWER_PATTERN = r"(?i)ANSWER\s*:\s*(Yes|No)"

MARKDOWN_PATTERN = r"```md(.*?)```"