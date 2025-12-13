# Test Projects for Omium Workflow Testing

This directory contains real workflow examples for testing Omium's workflow execution system.

## Files

- **`crewai_research_workflow.py`**: A CrewAI workflow that researches a topic and creates a report
- **`langgraph_calculator_workflow.py`**: A LangGraph workflow that performs arithmetic calculations

## Quick Start

### Prerequisites

1. Install required packages:
   ```bash
   pip install omium crewai crewai-tools langgraph langchain langchain-anthropic
   ```

2. Set up environment variables:
   ```bash
   export SERPER_API_KEY="your-serper-api-key"  # For CrewAI web search
   export ANTHROPIC_API_KEY="your-anthropic-api-key"  # For LangGraph
   export OMIUM_API_KEY="your-omium-api-key"
   export OMIUM_API_URL="https://api.omium.ai"
   ```

3. Initialize Omium SDK:
   ```bash
   omium init --api-key $OMIUM_API_KEY --api-url $OMIUM_API_URL
   ```

### Export Workflows

#### CrewAI Workflow

```bash
omium export-crew test-projects/crewai_research_workflow.py:research_crew \
  --workflow-name "Research Workflow" \
  --workflow-id "research-workflow" \
  -o test-projects/crewai_workflow.json
```

#### LangGraph Workflow

```bash
omium export-langgraph test-projects/langgraph_calculator_workflow.py:compiled_calculator_graph \
  --workflow-name "Calculator Workflow" \
  --workflow-id "calculator-workflow" \
  -o test-projects/langgraph_workflow.json
```

### Execute Workflows

#### Via CLI

```bash
# Execute CrewAI workflow
omium run test-projects/crewai_workflow.json

# Execute LangGraph workflow
omium run test-projects/langgraph_workflow.json
```

#### Via Frontend

1. Import the exported JSON file (`crewai_workflow.json` or `langgraph_workflow.json`)
2. Click "Execute" and provide input
3. Monitor execution status and results

## Workflow Details

### CrewAI Research Workflow

**Purpose**: Research a topic and create a comprehensive report

**Agents**:
- **Researcher**: Conducts research using web search tools
- **Reporting Analyst**: Creates detailed reports from research findings

**Input**: Topic (e.g., "Artificial Intelligence Agents")

**Output**: Research report with detailed sections

**Features**:
- Sequential task execution
- Web search integration (Serper.dev)
- Structured report generation

### LangGraph Calculator Workflow

**Purpose**: Perform arithmetic calculations using LLM and tools

**Nodes**:
- **llm_call**: LLM decides whether to call a tool
- **tool_node**: Executes arithmetic operations (add, multiply, divide)

**Input**: Calculation request (e.g., "Add 3 and 4, then multiply by 2")

**Output**: Calculation result

**Features**:
- Tool calling with LLM
- Conditional routing based on tool calls
- State management across nodes

## Testing Checklist

- [ ] Export workflows successfully
- [ ] Import workflows via frontend
- [ ] Execute workflows successfully
- [ ] Verify output data is correct
- [ ] Verify checkpoints are created
- [ ] Verify execution appears in frontend
- [ ] Test failure scenarios
- [ ] Test recovery from checkpoints

## Troubleshooting

### Export Fails

**Error**: `Could not find object 'research_crew' in file`

**Solution**: 
- Verify you're in the correct directory
- Check object name matches exactly (case-sensitive)
- Ensure object is defined at module level

### Execution Fails

**Error**: `Execution failed`

**Solution**:
- Check API keys are set correctly
- Verify Execution Engine is running
- Check execution logs: `omium show <execution-id>`

### No Checkpoints Created

**Solution**:
- Verify checkpoint manager is running
- Check execution metadata for checkpoint info
- Verify workflow adapter supports checkpointing

## Next Steps

See `../END_TO_END_WORKFLOW_TESTING_GUIDE.md` for comprehensive testing instructions.

