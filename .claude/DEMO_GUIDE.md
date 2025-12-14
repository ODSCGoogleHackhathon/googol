# MedAnnotator Demo Video Guide

## Video Link
📺 **[Demo Video Link - TO BE ADDED]**
https://your.video.link.here

## Demo Script (5 Minutes)

### Introduction (00:00–00:45)

**Show:**
- Opening screen with MedAnnotator title
- Team name: Googol
- Problem statement

**Say:**
> "Hi, I'm [Name] from Team Googol. We built MedAnnotator, an AI-powered medical image annotation tool that helps radiologists and medical professionals streamline the annotation process for chest X-rays and other medical images.
>
> The problem we're solving is that manual medical image annotation is time-consuming, inconsistent, and doesn't scale. Radiologists spend hours annotating images for training datasets, research, and quality control. Our solution uses Google Gemini and MedGemma to provide fast, structured, and consistent annotations while keeping humans in the loop."

---

### System Architecture Overview (00:45–01:15)

**Show:**
- Architecture diagram from ARCHITECTURE.md
- Quick tour of codebase structure

**Say:**
> "MedAnnotator uses a ReAct (Reasoning + Acting) agentic pattern. Here's how it works:
>
> 1. A Streamlit frontend provides an intuitive interface
> 2. A FastAPI backend handles requests
> 3. Our Gemini agent orchestrates the workflow
> 4. MedGemma (our medical specialist tool) analyzes the image
> 5. Gemini structures the output into standardized JSON
>
> This is truly agentic because the system reasons about the task, plans the approach, calls tools autonomously, and structures the output without manual intervention."

---

### Live Demo - Upload & Annotation (01:15–02:30)

**Show:**
- Streamlit UI
- Upload a chest X-ray image
- Add optional patient ID and instructions
- Click "Annotate Image"
- Show loading state

**Say:**
> "Let me show you how it works. I'm uploading a chest X-ray image. I can optionally add a patient ID and specific instructions like 'Focus on lung fields.'
>
> When I click 'Annotate Image,' watch what happens behind the scenes:
>
> Step 1: The agent receives the request and reasons about the task
> Step 2: It calls our MedGemma tool for specialized medical analysis
> Step 3: MedGemma returns detailed findings
> Step 4: The agent uses Gemini to structure this into standardized JSON
>
> And there we go! In just [X] seconds, we have a complete annotation."

---

### Results & Agentic Features (02:30–03:30)

**Show:**
- Structured annotation results
- Findings with labels, locations, and severity
- Confidence score
- JSON output
- Edit and download functionality

**Say:**
> "Here's what makes this agentic and powerful:
>
> 1. **Multi-step reasoning**: The agent broke down the complex task into steps
> 2. **Tool orchestration**: It knew to call MedGemma first, then structure with Gemini
> 3. **Structured output**: The JSON is consistent and follows our schema every time
> 4. **Human-in-the-loop**: Medical professionals can review and edit the findings
> 5. **Traceability**: Every decision is logged for audit purposes
>
> The findings include the label (like 'Normal' or 'Pneumothorax'), the anatomical location, and severity level. We also provide a confidence score.
>
> Medical professionals can edit the JSON directly if needed and download it for their records."

---

### Technical Deep Dive (03:30–04:15)

**Show:**
- Open logs to show agent reasoning
- Show code snippet of ReAct pattern
- Show health check endpoint

**Say:**
> "Let me show you the agent's reasoning process. In our logs, you can see:
> - Request received
> - MedGemma tool called
> - Analysis processed
> - JSON structured
> - Response returned
>
> Every step is logged and traceable. This is critical for medical applications where you need to understand how a decision was made.
>
> Our health check endpoint shows that both Gemini and MedGemma are connected and functioning."

---

### Innovation & Impact (04:15–04:45)

**Show:**
- Architecture diagram
- Key features list

**Say:**
> "What makes MedAnnotator innovative:
>
> 1. **Gemini Integration**: We use Gemini 2.0 Flash's JSON mode for reliable structured output
> 2. **ReAct Pattern**: True agentic behavior with reasoning and tool use
> 3. **Medical Specialization**: MedGemma brings domain expertise
> 4. **Scalability**: Can process thousands of images consistently
> 5. **Human-in-Loop**: Designed for real-world clinical workflows
>
> The societal impact is significant: faster research, better training datasets, and ultimately improved patient care through more efficient radiology workflows."

---

### Conclusion & Future (04:45–05:00)

**Show:**
- Final results
- Team credits

**Say:**
> "In conclusion, MedAnnotator demonstrates how agentic AI can solve real-world problems in healthcare. We've built a production-ready MVP in this hackathon.
>
> Future enhancements include RAG for medical guidelines, bounding box overlays, and integration with real MedGemma endpoints.
>
> Thank you! This is MedAnnotator by Team Googol."

---

## Timestamps (Template)

- **00:00–00:45** — Introduction & Problem Statement
- **00:45–01:15** — System Architecture Overview
- **01:15–02:30** — Live Demo: Upload & Annotation Process
- **02:30–03:30** — Results & Agentic Features Explanation
- **03:30–04:15** — Technical Deep Dive (Logs, Code, Health Check)
- **04:15–04:45** — Innovation, Gemini Integration & Societal Impact
- **04:45–05:00** — Conclusion & Future Enhancements

---

## Key Points to Emphasize

### Technical Excellence
- Clean code architecture
- Comprehensive error handling
- Logging and observability
- Pydantic validation
- Async API design

### Gemini Integration
- Using Gemini 2.0 Flash Exp
- JSON mode for structured output
- ReAct reasoning pattern
- Multi-step agentic workflow
- Tool orchestration

### Societal Impact
- Helps radiologists work faster
- Improves annotation consistency
- Enables better medical research
- Scales to thousands of images
- Human-in-the-loop design
