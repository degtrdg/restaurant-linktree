npx create-next-app@latest gene-stepper --typescript --tailwind --eslint

- yes to src directory

npx shadcn-ui@latest init

add with normal shad way
https://ui.shadcn.com/docs/installation/next

https://codevoweb.com/integrate-fastapi-framework-with-nextjs-and-deploy/

activate conda base with version of python you like

```sh
conda activate 311

python -m venv venv

source venv/bin/activate

conda deactivate

pip install -r requirements.txt

npm install
```

Prompt

We are looking at a research proposal and a weakness of the proposal given by a reviewer. We'll be looking at the proposal a couple of paragraphs at a time and see if the paragraphs needs to be revised to address the weakness. If the paragraphs don't need to be changed, do not give an edit. Maintain the exact style and wording unless the change addresses the weakness.

Paragraph:

```md

```

Weakness

```md

```

Output the revised paragraph. Your revision based on the weakness should be in a md codeblock like you've seen above. Give an empty md codeblock if there should be no edit. Think step by step before giving your edit.

````

Have it reason Yes or No for if the paragraph is relevant
If Yes, do something about it.

We are looking at a research proposal and a weakness of the proposal given by a reviewer. We'll be looking at the proposal a paragraphs at a time and see if the paragraph needs to be revised to address the weakness.

Paragraph:

```md

````

Weakness

```md

```

Think step by step if the paragraph needs to be changed or not with respect to the given weakness. The last line of your response should be of the following format: 'ANSWER: $YESORNO' (without quotes) where YESORNO is one of Yes or No.

```

```

We need to think through what structure we want to make the data

- input:
  - weakness
    - input field
    - single weakness
  - essay
    - file input
    - split on frontend
    - send request for each paragraph
    - show original in input field and new in right
