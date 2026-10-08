# Workflow DSL

Shape of a blank export; values vary. Taken from a real console export (`api/tests/fixtures/workflow/simple_passthrough_workflow.yml`), trimmed to a Start node wired to an End node.

## Where things go

- Top level: `version`, `kind: app`, `app` (name, mode, icon), `dependencies`, `workflow`.
- `workflow.graph.nodes[]`: `{id, type: custom, data: {type, title, ...}, position: {x, y}}`. `data.type` is the node type; the rest of `data` comes from `describe node_type`.
- `workflow.graph.edges[]`: `{id, source, target, sourceHandle: source, targetHandle: target, data: {sourceType, targetType}}`. Branch nodes use another `sourceHandle`.
- `workflow.features`, `workflow.environment_variables`, `workflow.conversation_variables`: keep what the export gave you.
- A node id is any unique string. Never change the id of an existing node.
- Read another node's output as `{{#<node_id>.<var>#}}` in text fields. In `value_selector` write `[<node_id>, <var>]`.
- Never put secret values in the DSL.

## Example

```yaml
version: 0.3.1
kind: app
app:
  name: echo
  mode: workflow
  icon: 🤖
  icon_background: '#FFEAD5'
  description: ''
  use_icon_as_answer_icon: false
dependencies: []
workflow:
  conversation_variables: []
  environment_variables: []
  features:
    file_upload: { enabled: false }
    opening_statement: ''
    retriever_resource: { enabled: true }
    sensitive_word_avoidance: { enabled: false }
    speech_to_text: { enabled: false }
    suggested_questions: []
    suggested_questions_after_answer: { enabled: false }
    text_to_speech: { enabled: false, language: '', voice: '' }
  graph:
    nodes:
      - id: '1754154032319'
        type: custom
        position: { x: 30, y: 227 }
        data:
          type: start
          title: Start
          desc: ''
          variables:
            - {
                variable: query,
                label: query,
                type: text-input,
                required: true,
                max_length: null,
                options: [],
              }
      - id: '1754154034161'
        type: custom
        position: { x: 334, y: 227 }
        data:
          type: end
          title: End
          desc: ''
          outputs:
            - { variable: query, value_type: string, value_selector: ['1754154032319', query] }
    edges:
      - id: 1754154032319-source-1754154034161-target
        type: custom
        source: '1754154032319'
        sourceHandle: source
        target: '1754154034161'
        targetHandle: target
        data: { sourceType: start, targetType: end }
```
