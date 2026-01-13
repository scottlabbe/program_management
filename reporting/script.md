## Video Outline

### 1. Opening hook (1 min)

Show slide 1. 

This is the final step in the cost report/ desk review automation process with OpenAI's coding model named Codex. 

In earlier videos I used Codex to extract salary data from a folder of spreadsheets, saved it into a database, and performed simple testing procedures on the salary data from the database. 

In this step, we're turning desk-reviewed data into district reimbursement packets, including reimbursement summary letters and a list of the findings identified in the desk review procedures, ready to send to the district so they can be reimbursed for their expenses. 

Codex is a coding agent used in the terminal application. It's a very powerful tool that writes code to folders you can take to your own environment to run securely. 

Same idea here as the whole series: we're not asking the AI to write anything. We're pointing it at templates, with all the context it needs, and telling it where to fill in the blanks.

### 2. Show the inputs (3 min)
- **The templates** I created these templates after planning this step with the help of ChatGPT. Since I'm using python, I'm using the jinja library for the placeholders I need data filled in. 

This is where the district specific data will be filled in with the python code. 

– Open both Word docs. Highlight the Jinja library for the placeholders: `{{ district_name }}`, `{{ state_salary_total }}`, the findings loop, no links just text that will be read by the python code during the main process. 

These are the simplified versions of the templates I've seen used in real-world government programs. For this experiment, the AI model doesn't touch the wording—it just fills in values.

### 3. Walk through the prompt (4 min)
- Explain the structure: Context → Goal → Outputs → Implementation notes

The prompt includes, the overall goal of this step, the location of the data and templates, the database fields I need to use in the templates, and where the templates are located. 

What I'm trying to do with this prompt is narrow the lane that they agent will operate in. I'm telling it about the relevant existing data (database tables, templates)

It also includes the file strucure I want in the output, the constraints I want it to follow, and some other notes that will help it generate functions in readable groups. 

### 4. Run the agent (5-7 min)
- Paste the prompt, let it generate the script
- Light narration as it works: what it's doing, any interesting choices it makes
- If it asks clarifying questions or makes mistakes, show that—it's real

### 5. Inspect the outputs (3 min)
- Open one district folder
- Show the filled-in Word doc side by side with the template
- Open the PDF—confirm it rendered correctly
- Spot-check one or two values against the database

### 6. Wrap-up / series reflection (2 min)
Use your closing paragraph from Option A or B—the contrast between the 6-report demo and the real 400-report engagement. End with: "The structure you already have is the raw material. Use it."

So think about what we've done, we had a folder of spreadsheets that mimiced real-world cost reporting data, we built an extraction, validation, and desk review pipeline, and with this last step, we build a reporting process that prepares the desk reviewed data into reports ready to send to districts. 

One thing that became clear throughout this project how much these models can accomplish with the right direction and careful planning. If I take a step back, I taped this walkthough to demonstrate how easy it is to build a python pipeline that autoated significant amounts of work I've led teams of people to complete in the past. This would allow me or anyone or any organization who went through these steps to have their own code that they could use and modiify as needed to accomplish these tasks. 

When you look at the output, the model actually did all the work on the test data. If there was a way my organization was able to clear using this kind of data in the AI model subscription we paid for, and we could provide this data securly to the model, AI could just do all the work of extracting, reviewing, testing, and reporting on the data. It's actually kind of crazy to think about what can be accomplished with these coding agnets. 

---
