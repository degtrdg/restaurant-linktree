"use client";
import { defaultFile } from "./text";

import { useState, ChangeEvent, FormEvent, useEffect } from "react";

type EssayParagraph = {
  original: string;
  processed: string | null;
  revised: string | null;
};

type ResponseBody = {
  original: string;
  revised: string;
  diff_html: string;
};

type DiffDisplayProps = {
  content: string | null;
};

const DiffDisplay = ({ content }: DiffDisplayProps) => (
  <div
    className="prose p-2 border rounded w-full h-auto min-h-[4rem] whitespace-pre-wrap"
    dangerouslySetInnerHTML={{ __html: content || "Loading..." }}
  />
);

const Home: React.FC = () => {
  const [weakness, setWeakness] = useState(
    "The biological effect of any given target site may be cell context dependent. How to generalize the knowledge, especially for understanding the immune side effect in the clinical trial, is a question."
  );
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [paragraphs, setParagraphs] = useState<EssayParagraph[]>([]);

  useEffect(() => {
    // Simulate setting file content from an auto-uploaded file
    setFileContent(defaultFile);
    // Split the default file content into paragraphs and set it
    const paragraphs = defaultFile.split("\n\n").map((paragraph) => ({
      original: paragraph,
      processed: null,
      revised: null,
    }));
  }, []); // Empty dependency array to run only once on mount

  const handleWeaknessChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setWeakness(e.target.value);
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setParagraphs([]); // Clear out existing paragraphs
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event: ProgressEvent<FileReader>) => {
        if (event.target?.result) {
          setFileContent(event.target.result.toString());
        }
      };
      reader.readAsText(file);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    // Check if paragraphs are already processed
    if (paragraphs.length > 0) {
      // Use the current paragraphs' original text for reprocessing
      processParagraphs(paragraphs);
    } else if (fileContent) {
      // If no paragraphs processed yet, parse file content
      const parsedParagraphs = fileContent.split("\n\n").map((paragraph) => ({
        original: paragraph,
        processed: null,
        revised: null,
      }));
      setParagraphs(parsedParagraphs);
      processParagraphs(parsedParagraphs);
    }
  };

  const processParagraphs = async (paragraphs: EssayParagraph[]) => {
    // Determine the base URL based on the environment
    const baseUrl =
      process.env.NODE_ENV === "development"
        ? "http://localhost:8000"
        : "https://proposal-reviewer-production.up.railway.app";
    for (let index = 0; index < paragraphs.length; index++) {
      const paragraph = paragraphs[index];
      try {
        const response = await fetch(`${baseUrl}/api/process`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            paragraph: paragraph.original,
            weakness: weakness,
          }),
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: ResponseBody = await response.json();
        setParagraphs((prev) => {
          const newParagraphs = [...prev];
          newParagraphs[index].processed = data.diff_html;
          newParagraphs[index].revised = data.revised;
          return newParagraphs;
        });
      } catch (error) {
        console.error("Failed to process paragraph:", error);
        setParagraphs((prev) => {
          const newParagraphs = [...prev];
          newParagraphs[index].processed = "Error processing paragraph.";
          newParagraphs[index].revised = "";
          return newParagraphs;
        });
      }
    }
  };

  return (
    <div className="container mx-auto p-4 grid grid-cols-1 gap-4">
      <div className="text-2xl font-bold mb-4">Proposal Review</div>
      <ul className="list-disc list-inside mb-4">
        <li>Input a file that has the proposal.</li>
        <li>
          Have the text file with separate paragraphs with an empty line, like
          so:
          <ul className="list-disc list-inside ml-5">
            <br />
            <div>Paragraph 1</div>
            <br />
            <div>Paragraph 2</div>
            <br />
            <div>Paragraph 3</div>
            <br />
            <div>etc. </div>
            <br />
          </ul>
        </li>
        <li>Write down the weakness.</li>
        <li>Submit.</li>
        <li>
          There is an example proposal already there along with a weakness.
        </li>
        <li>
          You can change the paragraph on the left based on the edits you see on
          the right and run the check again by pressing submit
        </li>
      </ul>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label
            htmlFor="fileInput"
            className="block text-sm font-medium text-gray-700"
          >
            Upload a file (text.txt is loaded by default and you can just press
            submit if you'd like):
          </label>
          <input
            id="fileInput"
            type="file"
            onChange={handleFileChange}
            className={`block w-full text-sm
      file:py-2 file:px-4
      file:rounded file:border-0
      file:text-sm file:font-semibold
      file:bg-violet-50 file:text-violet-700
    `}
          />
        </div>
        <div>
          <textarea
            value={weakness}
            onChange={handleWeaknessChange}
            placeholder=""
            rows={Math.max(4, weakness.split("\n").length)}
            className="p-2 border rounded w-full h-1/2"
          />
          <button
            onClick={handleSubmit}
            className="mt-2 p-2 bg-blue-500 text-white rounded w-full"
          >
            Submit
          </button>
        </div>
      </div>
      <div>
        {paragraphs.map((paragraph, index) => (
          <div
            key={index}
            className="grid grid-cols-2 gap-4 items-start p-1 relative group"
          >
            <textarea
              value={paragraph.original}
              onChange={(e) => {
                const updatedValue = e.target.value;
                setParagraphs((prevParagraphs) => {
                  return prevParagraphs.map((p, i) => {
                    if (i === index) {
                      return { ...p, original: updatedValue };
                    }
                    return p;
                  });
                });
              }}
              className="w-full h-full"
            ></textarea>
            <div>
              <DiffDisplay content={paragraph.processed} />
              <button
                onClick={() => {
                  navigator.clipboard
                    .writeText(paragraph.revised || "")
                    .then(() => {
                      console.log("Text copied to clipboard");
                    })
                    .catch((err) => {
                      console.error("Failed to copy text: ", err);
                    });
                }}
                className="mt-2 p-2 bg-blue-500 text-white rounded w-full"
              >
                Copy Revised Text
              </button>
            </div>
            <div>
              <span className="text-green-500"> </span>
              <span className="text-red-500"> </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Home;
