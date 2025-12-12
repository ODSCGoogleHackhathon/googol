# Team Googol - Task Distribution

## Team Members

1. **Rafael Kovashikawa** (rkovashikawa@gmail.com) - GitHub: kovashikawa
2. **Ravali Yerrapothu** (yravali592@gmail.com) - GitHub: ry639a
3. **Tyrone** (email TBD)
4. **Guilherme** (guirque@gmail.com) - GitHub: guirque

## Role Assignments

### Role 1: Frontend Lead (Streamlit UI)
**Assigned to:** TBD

**Responsibilities:**
- Streamlit interface development
- Image upload functionality
- Results display and visualization
- JSON editor integration
- Download functionality

**Files to Work On:**
- `src/ui/app.py`
- `src/schemas.py` (for understanding data models)

**Key Tasks:**
- [x] Create image upload widget
- [x] Display uploaded images
- [x] Build annotation results display
- [ ] Add patient ID and prompt inputs
- [ ] Implement JSON editor
- [ ] Add download button
- [ ] Polish UI/UX
- [ ] Test with various image sizes

**Estimated Time:** 6-8 hours

---

### Role 2: Backend Lead (FastAPI)
**Assigned to:** TBD

**Responsibilities:**
- FastAPI endpoint development
- Request/response validation
- Error handling
- Backend health monitoring
- CORS configuration

**Files to Work On:**
- `src/api/main.py`
- `src/schemas.py`
- `src/config.py`

**Key Tasks:**
- [x] Set up FastAPI application
- [x] Create /annotate endpoint
- [x] Create /health endpoint
- [x] Add CORS middleware
- [ ] Test endpoints with Postman/curl
- [ ] Add comprehensive error handling
- [ ] Optimize response times
- [ ] Add request logging

**Estimated Time:** 6-8 hours

---

### Role 3: LLM Orchestration Lead (Gemini Agent)
**Assigned to:** TBD

**Responsibilities:**
- Gemini API integration
- ReAct pattern implementation
- Prompt engineering
- JSON structuring logic
- Error recovery

**Files to Work On:**
- `src/agent/gemini_agent.py`
- `src/config.py`
- `src/schemas.py`

**Key Tasks:**
- [x] Set up Gemini API connection
- [x] Implement ReAct reasoning pattern
- [x] Create structured output prompts
- [x] Add JSON parsing logic
- [x] Implement fallback mechanisms
- [ ] Test with various medical analyses
- [ ] Optimize prompts for accuracy
- [ ] Handle edge cases

**Estimated Time:** 8-10 hours

---

### Role 4: Tools & DevOps Lead (MedGemma + Deployment)
**Assigned to:** TBD

**Responsibilities:**
- MedGemma tool development
- Mock data implementation
- Sample data preparation
- Deployment scripts
- Documentation
- Demo preparation

**Files to Work On:**
- `src/tools/medgemma_tool.py`
- `PROJECT_SETUP.md`
- `DEMO.md`
- `run_backend.sh`, `run_frontend.sh`
- `data/` directory

**Key Tasks:**
- [x] Implement MedGemma mock tool
- [x] Create realistic medical analysis responses
- [ ] Gather sample medical images
- [ ] Test end-to-end workflow
- [ ] Create deployment documentation
- [ ] Prepare demo script
- [ ] Record demo video
- [ ] Final testing and bug fixes

**Estimated Time:** 8-10 hours

---

## Shared Responsibilities (All Team Members)

### Phase 1: Setup (First 2 hours)
- [ ] All: Clone repository
- [ ] All: Set up Python environment
- [ ] All: Get Google API keys
- [ ] All: Run the application locally
- [ ] All: Verify can access frontend and backend

### Phase 2: Core Development (Hours 2-12)
- [ ] Each: Work on assigned role tasks
- [ ] All: Daily sync meetings
- [ ] All: Push code regularly to GitHub
- [ ] All: Help teammates with blockers

### Phase 3: Integration & Testing (Hours 12-16)
- [ ] All: End-to-end testing
- [ ] All: Bug fixing
- [ ] All: Code review
- [ ] All: Performance optimization

### Phase 4: Polish & Demo (Hours 16-20)
- [ ] All: UI/UX improvements
- [ ] All: Documentation updates
- [ ] Assigned lead: Record demo video
- [ ] All: Prepare pitch presentation
- [ ] All: Final testing

---

## Communication Protocol

### Daily Standups
- Time: TBD
- Format: 5 minutes per person
  - What I did yesterday
  - What I'm doing today
  - Any blockers

### Code Reviews
- All pull requests require 1 review
- Review within 2 hours
- Test locally before approving

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Description of changes"

# Push to GitHub
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

### Branch Naming Convention
- `feature/frontend-image-upload`
- `feature/backend-health-check`
- `feature/agent-react-pattern`
- `feature/medgemma-mock`
- `bugfix/cors-error`
- `docs/update-readme`

---

## Milestones & Deadlines

### Milestone 1: MVP Working (Day 1 Evening)
- [x] Backend server running
- [x] Frontend displays
- [x] Can upload image
- [ ] Can get annotation response
- [ ] Basic error handling

### Milestone 2: Full Features (Day 2 Morning)
- [ ] All UI features complete
- [ ] All API endpoints working
- [ ] ReAct agent functioning
- [ ] Sample data added
- [ ] Logging working

### Milestone 3: Polish (Day 2 Afternoon)
- [ ] UI/UX polished
- [ ] Error handling robust
- [ ] Documentation complete
- [ ] Demo video recorded

### Milestone 4: Submission (Day 2 Evening)
- [ ] Final testing complete
- [ ] All documentation updated
- [ ] Demo video uploaded
- [ ] README.md polished
- [ ] Submission completed

---

## Resources for Team

### API Keys
- Google Gemini: https://makersuite.google.com/app/apikey
- Store in `.env` file (never commit!)

### Documentation
- Gemini API: https://ai.google.dev/docs
- FastAPI: https://fastapi.tiangolo.com/
- Streamlit: https://docs.streamlit.io/
- Pydantic: https://docs.pydantic.dev/

### Sample Code & Tutorials
- ReAct Pattern: https://arxiv.org/abs/2210.03629
- Function Calling: https://ai.google.dev/docs/function_calling
- Medical AI Ethics: https://www.fda.gov/medical-devices/software-medical-device-samd

---

## Questions & Support

- Technical issues: Post in team Slack/Discord
- Git issues: Ask DevOps lead
- API issues: Ask LLM lead
- UI issues: Ask Frontend lead

## Success Metrics

- [ ] Application runs without errors
- [ ] Can annotate a medical image in <5 seconds
- [ ] JSON output is valid and structured
- [ ] UI is intuitive and clean
- [ ] Documentation is comprehensive
- [ ] Demo video is clear and compelling
- [ ] All team members can explain the system
