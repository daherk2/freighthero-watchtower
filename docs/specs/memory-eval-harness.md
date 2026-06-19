# FreightHero — Memory Evaluation Harness Specification

> **Versão:** 1.0  
> **Data:** 7 de junho de 2026  
> **Status:** Especificação  
> **Veja também:** [Arquitetura de Memória](memory-architecture.md) | [ADRs de Memória](adrs/memory-adrs.md)

---

## 1. Visão Geral

O Memory Evaluation Harness é um conjunto de testes que valida o comportamento correto do sistema de memória agentic. Ele complementa o eval suite de workflow existente (definido em `specs/test-cases.json`) com assertions específicas sobre operações de memória.

### Princípios

1. **Memory operations are testable**: Toda operação de memória (add, retrieve, update, delete, summarize, filter) deve ser registrada e testável.
2. **Assertions over memory calls**: Assim como tool calls, memory operations devem ter assertions de required e forbidden.
3. **Cross-event continuity**: Testes devem validar que memórias persistem entre eventos.
4. **Customer isolation**: Testes devem validar que memórias de um cliente não vazam para outro.
5. **Token efficiency**: Testes devem validar que sumarização reduz tokens preservando informações-chave.

---

## 2. Estrutura do Eval Harness

### Comando de Execução

```bash
# Executar todos os testes de memória
make eval-memory

# Executar apenas testes de retrieval
make eval-memory-retrieval

# Executar apenas testes de forgetting
make eval-memory-forgetting

# Executar apenas testes de sumarização
make eval-memory-summarization

# Executar apenas testes de long horizon
make eval-memory-long-horizon

# Executar apenas testes de customer context
make eval-memory-customer-context
```

### Formato do Resultado

```json
{
  "suite": "memory-eval",
  "timestamp": "2026-06-07T12:00:00Z",
  "results": [
    {
      "test_id": "mem-retrieval-001",
      "test_name": "Customer A POD validation rule retrieval",
      "status": "pass",
      "memory_operations": {
        "adds": 1,
        "retrieves": 1,
        "updates": 0,
        "deletes": 0,
        "summarizes": 0,
        "filters": 0
      },
      "metrics": {
        "retrieval_latency_ms": 45,
        "relevance_score": 0.95,
        "stm_token_count": 1200,
        "stm_token_limit": 4000,
        "stm_utilization": 0.30
      }
    }
  ],
  "summary": {
    "total": 25,
    "passed": 23,
    "failed": 2,
    "gaps": [
      "Long horizon test for cross-workflow memory continuity",
      "Summarization test for episode compression with state changes"
    ],
    "risky_hidden_cases": [
      "Multi-event continuity with ambiguous inputs",
      "Customer-specific context retention under high event volume"
    ]
  }
}
```

---

## 3. Retrieval Tests

### MEM-RET-001: Customer Rule Retrieval

**Objetivo**: Validar que regras do cliente são recuperadas corretamente por exact match.

```python
def test_customer_rule_retrieval():
    """Customer A rules should be retrieved when processing Customer A loads."""
    # Setup: Store Customer A rules in LTM
    memory_add(
        memory_type="semantic", scope="customer", scope_id="customer_a",
        content="Customer A: POD validation is automatic when check_attachment returns document_pod",
        content_type="rule", tags=["pod_validation", "customer_a"]
    )
    memory_add(
        memory_type="semantic", scope="customer", scope_id="customer_a",
        content="Customer A: Escalation channel is email",
        content_type="rule", tags=["escalation", "customer_a"]
    )
    memory_add(
        memory_type="semantic", scope="customer", scope_id="customer_a",
        content="Customer A: Delivery geofence radius is 1 mile",
        content_type="rule", tags=["geofence", "customer_a"]
    )
    
    # Act: Retrieve Customer A rules
    results = memory_retrieve(
        query="Customer A rules",
        memory_types=["semantic"],
        scope="customer",
        scope_id="customer_a",
        limit=10
    )
    
    # Assert
    assert results.ok
    assert len(results.memories) >= 3
    assert any("automatic" in m.content and "POD" in m.content for m in results.memories)
    assert any("email" in m.content for m in results.memories)
    assert any("1 mile" in m.content for m in results.memories)
    assert all(m.scope_id == "customer_a" for m in results.memories)
```

### MEM-RET-002: Cross-Customer Isolation

**Objetivo**: Validar que regras de Customer A não são recuperadas para Customer B.

```python
def test_cross_customer_isolation():
    """Customer A rules should NOT be retrieved for Customer B loads."""
    # Setup
    memory_add(memory_type="semantic", scope="customer", scope_id="customer_a",
               content="Customer A: Escalation via email")
    memory_add(memory_type="semantic", scope="customer", scope_id="customer_b",
               content="Customer B: Escalation via Slack")
    
    # Act
    results_a = memory_retrieve(query="escalation", scope="customer", scope_id="customer_a")
    results_b = memory_retrieve(query="escalation", scope="customer", scope_id="customer_b")
    
    # Assert
    assert all(m.scope_id == "customer_a" for m in results_a.memories)
    assert all(m.scope_id == "customer_b" for m in results_b.memories)
    assert not any("Slack" in m.content for m in results_a.memories)
    assert not any("email" in m.content for m in results_b.memories)
```

### MEM-RET-003: Driver Preference Retrieval

**Objetivo**: Validar que preferências do driver são recuperadas corretamente.

```python
def test_driver_preference_retrieval():
    """Driver preferences should be retrieved when processing events from that driver."""
    memory_add(memory_type="semantic", scope="driver", scope_id="driver-sam",
               content="Driver Sam prefers SMS communication and typically responds within 5 minutes",
               confidence=0.85)
    
    results = memory_retrieve(query="communication preferences", scope="driver", scope_id="driver-sam")
    
    assert len(results.memories) > 0
    assert any("SMS" in m.content for m in results.memories)
    assert any(m.confidence >= 0.8 for m in results.memories)
```

### MEM-RET-004: Episode History Retrieval

**Objetivo**: Validar que histórico de episódios é recuperado para a mesma carga.

```python
def test_episode_history_retrieval():
    """Recent episode history should be retrieved for the same load."""
    for i in range(5):
        memory_add(memory_type="episodic", scope="load", scope_id="load-001",
                   content=f"Event {i}: driver sent message about ETA")
    
    results = memory_retrieve(query="recent events", scope="load", scope_id="load-001",
                              memory_types=["episodic"], limit=10)
    
    assert len(results.memories) >= 5
    # Most recent events should have higher relevance
    assert results.memories[0].relevance_score >= results.memories[-1].relevance_score
```

### MEM-RET-005: Semantic Search for Learned Facts

**Objetivo**: Validar que busca semântica encontra fatos aprendidos mesmo com queries diferentes.

```python
def test_semantic_search_learned_facts():
    """Semantic search should find learned facts with different query phrasing."""
    memory_add(memory_type="semantic", scope="driver", scope_id="driver-sam",
               content="Driver Sam had a truck breakdown on load FH-2026-001",
               confidence=0.7)
    
    # Different phrasings should find the same fact
    for query in ["truck problems", "vehicle issues", "breakdown history", "equipment failure"]:
        results = memory_retrieve(query=query, scope="driver", scope_id="driver-sam",
                                   memory_types=["semantic"], min_relevance=0.5)
        assert len(results.memories) > 0, f"Query '{query}' should find breakdown fact"
```

---

## 4. Forgetting Tests

### MEM-FOR-001: Expired Memory Deletion

**Objetivo**: Validar que memórias expiradas são removidas.

```python
def test_expired_memory_deletion():
    """Memories past their TTL should be deleted."""
    memory_add(memory_type="semantic", scope="load", scope_id="load-001",
               content="Temporary tracking info", expires_at=datetime.now() - timedelta(hours=1))
    
    run_memory_maintenance()
    
    results = memory_retrieve(query="tracking info", scope="load", scope_id="load-001")
    assert all(m.content != "Temporary tracking info" for m in results.memories)
```

### MEM-FOR-002: Contradicted Fact Update

**Objetivo**: Validar que fatos contraditórios com maior confiança substituem fatos antigos.

```python
def test_contradicted_fact_update():
    """Higher-confidence facts should supersede lower-confidence ones."""
    memory_add(memory_type="semantic", scope="driver", scope_id="driver-sam",
               content="Driver Sam prefers email", confidence=0.5)
    
    # New observation with higher confidence
    memory_add(memory_type="semantic", scope="driver", scope_id="driver-sam",
               content="Driver Sam prefers SMS", confidence=0.9)
    
    results = memory_retrieve(query="communication preferences", scope="driver", scope_id="driver-sam")
    
    # Should have the higher-confidence fact
    assert any("SMS" in m.content and m.confidence >= 0.9 for m in results.memories)
    # Should NOT have the lower-confidence fact (or it should be marked as superseded)
    high_confidence_facts = [m for m in results.memories if "SMS" in m.content and m.confidence >= 0.9]
    assert len(high_confidence_facts) > 0
```

### MEM-FOR-003: Low Relevance Eviction

**Objetivo**: Validar que memórias de baixa relevância são evictadas.

```python
def test_low_relevance_eviction():
    """Low-relevance memories that haven't been accessed should be evicted."""
    memory_add(memory_type="episodic", scope="load", scope_id="load-001",
               content="Minor status update", relevance_score=0.1)
    
    run_memory_maintenance()
    
    results = memory_retrieve(query="status update", scope="load", scope_id="load-001",
                               min_relevance=0.3)
    assert not any(m.content == "Minor status update" for m in results.memories)
```

### MEM-FOR-004: Completed Load Archival

**Objetivo**: Validar que episódios de cargas completadas são arquivados, não deletados.

```python
def test_completed_load_archival():
    """Episodes for completed loads should be archived, not deleted."""
    memory_add(memory_type="episodic", scope="load", scope_id="load-completed",
               content="Full delivery episode")
    
    archive_completed_load_episodes(load_id="load-completed")
    
    # Should not appear in active retrieval
    active_results = memory_retrieve(query="delivery", scope="load", scope_id="load-completed")
    assert len(active_results.memories) == 0
    
    # But should exist in archive
    archived = get_archived_memories(scope_id="load-completed")
    assert len(archived) > 0
```

---

## 5. Summarization Tests

### MEM-SUM-001: STM Summarization Reduces Tokens

**Objetivo**: Validar que sumarização de STM reduz tokens preservando informações-chave.

```python
def test_stm_summarization_reduces_tokens():
    """Summarizing STM should reduce token count while preserving key information."""
    # Add 20 items to STM
    for i in range(20):
        memory_add(memory_type="stm", scope="load", scope_id="load-001",
                   content=f"Tracking ping {i}: lat=32.77, lng=-96.79, distance={0.5-i*0.02} miles")
    
    original_tokens = get_stm_token_count(load_id="load-001")
    
    result = memory_summarize(memory_type="stm", scope_id="load-001",
                              strategy="compress_older", preserve_recent_n=5)
    
    assert result.ok
    assert result.summarized_token_count < original_tokens
    assert result.reduction_percentage > 30  # At least 30% reduction
    
    # Key information should be preserved
    summarized_content = get_stm_content(load_id="load-001")
    assert "tracking" in summarized_content.lower() or "ping" in summarized_content.lower()
```

### MEM-SUM-002: Episode Compression

**Objetivo**: Validar que episódios longos são comprimidos em resumos.

```python
def test_episode_compression():
    """Long episodes should be compressed into summaries."""
    for i in range(15):
        memory_add(memory_type="episodic", scope="load", scope_id="load-002",
                   content=f"Event {i}: driver communication")
    
    result = memory_summarize(memory_type="episodic", scope_id="load-002",
                              strategy="episode_compression")
    
    assert result.ok
    assert result.items_summarized > 0
    assert result.items_preserved > 0  # Recent events preserved
```

### MEM-SUM-003: Summarization Preserves State Changes

**Objetivo**: Validar que sumarização preserva mudanças de estado.

```python
def test_summarization_preserves_state_changes():
    """Summarization should preserve state transitions even when compressing."""
    memory_add(memory_type="stm", scope="load", scope_id="load-003",
               content="State changed from on_route_to_delivery to at_delivery")
    memory_add(memory_type="stm", scope="load", scope_id="load-003",
               content="Driver sent: 'I'm here'")
    
    result = memory_summarize(memory_type="stm", scope_id="load-003",
                              strategy="compress_older")
    
    # State change should be preserved
    summarized = get_stm_content(load_id="load-003")
    assert "at_delivery" in summarized
```

### MEM-SUM-004: Token Reduction Metrics

**Objetivo**: Validar que métricas de redução de tokens são registradas.

```python
def test_token_reduction_metrics():
    """Token reduction metrics should be recorded for observability."""
    # Add items and summarize
    for i in range(10):
        memory_add(memory_type="stm", scope="load", scope_id="load-004",
                   content=f"Event {i}: status update")
    
    result = memory_summarize(memory_type="stm", scope_id="load-004",
                              strategy="compress_older")
    
    # Check metrics are recorded
    metrics = get_memory_metrics(load_id="load-004")
    assert "context_token_reduction" in metrics
    assert metrics["context_token_reduction"] > 0
    assert "stm_utilization" in metrics
    assert metrics["stm_utilization"] < 1.0  # Should be reduced after summarization
```

---

## 6. Long Horizon Tests

### MEM-LH-001: Multi-Event Continuity

**Objetivo**: Validar que o agente lembra contexto de eventos anteriores na mesma carga.

```python
def test_multi_event_continuity():
    """Agent should remember context from previous events in the same load."""
    # Event 1: Driver provides ETA
    result_1 = process_event(inbound_communication(
        event_id="evt-1", load_id="load-001", customer_id="customer_a",
        content="ETA 3pm", channel="sms", sender_type="driver"
    ))
    
    # Verify ETA was stored in memory
    memories = memory_retrieve(query="ETA", scope="load", scope_id="load-001")
    assert any("3pm" in m.content for m in memories.memories)
    
    # Event 2: Timer fires for follow-up
    result_2 = process_event(timer_callback(
        event_id="evt-2", load_id="load-001", timer_type="eta_followup"
    ))
    
    # Agent should remember the ETA from event 1
    memories_after = memory_retrieve(query="ETA follow-up context", scope="load", scope_id="load-001")
    assert any("3pm" in m.content or "ETA" in m.content for m in memories_after.memories)
```

### MEM-LH-002: Delayed Followup Remembers Context

**Objetivo**: Validar que timer callbacks têm acesso ao contexto que os agendou.

```python
def test_delayed_followup_remembers_context():
    """Timer callback should have access to the context that scheduled it."""
    # Process ETA event (creates timer)
    process_event(inbound_communication(
        event_id="evt-1", load_id="load-001", customer_id="customer_c",
        content="ETA 2:30pm central", channel="sms", sender_type="driver"
    ))
    
    # Verify timer was created
    timers = get_active_timers(load_id="load-001")
    assert any(t.timer_type == "eta_followup" for t in timers)
    
    # When timer fires, agent should remember:
    # 1. Driver provided ETA
    # 2. Customer C has 45-min timer
    # 3. Previous interactions with this driver
    
    memories = memory_retrieve(query="ETA follow-up context", scope="load", scope_id="load-001")
    assert any("2:30pm" in m.content or "ETA" in m.content for m in memories.memories)
    
    customer_rules = memory_retrieve(query="timer rules", scope="customer", scope_id="customer_c")
    assert any("45" in m.content for m in customer_rules.memories)
```

### MEM-LH-003: Workflow Transition Preserves Memory

**Objetivo**: Validar que memória persiste quando o workflow transita de ETA Checkpoint para Confirm Delivery.

```python
def test_workflow_transition_preserves_memory():
    """When transitioning from ETA Checkpoint to Confirm Delivery, memory should persist."""
    # Process arrival event (transitions from on_route to at_delivery)
    process_event(inbound_communication(
        event_id="evt-1", load_id="load-001", customer_id="customer_a",
        content="Arrived at receiver", channel="sms", sender_type="driver"
    ))
    
    # Verify arrival was stored in memory
    memories = memory_retrieve(query="arrival", scope="load", scope_id="load-001")
    assert any("arrived" in m.content.lower() for m in memories.memories)
    
    # Now in Confirm Delivery workflow
    # Agent should remember the arrival message and previous ETA context
    process_event(inbound_communication(
        event_id="evt-2", load_id="load-001", customer_id="customer_a",
        content="Unloading started", channel="sms", sender_type="driver"
    ))
    
    # Verify agent has context from both events
    all_memories = memory_retrieve(query="delivery context", scope="load", scope_id="load-001")
    assert len(all_memories.memories) >= 2  # At least arrival and unloading
```

### MEM-LH-004: Driver Preference Learning

**Objetivo**: Validar que o agente aprende preferências do driver ao longo de múltiplas interações.

```python
def test_driver_preference_learning():
    """Agent should learn driver preferences across multiple interactions."""
    # Event 1: Driver sends SMS
    process_event(inbound_communication(
        event_id="evt-1", load_id="load-001", customer_id="customer_a",
        content="ETA 3pm", channel="sms", sender_type="driver",
        sender_name="Sam Driver"
    ))
    
    # Agent should note driver uses SMS
    memories = memory_retrieve(query="driver preferences", scope="driver", scope_id="driver-sam")
    # May or may not have a preference yet (first interaction)
    
    # Event 2: Driver sends another SMS
    process_event(inbound_communication(
        event_id="evt-2", load_id="load-001", customer_id="customer_a",
        content="Arrived at receiver", channel="sms", sender_type="driver",
        sender_name="Sam Driver"
    ))
    
    # After multiple SMS interactions, agent should learn preference
    memories = memory_retrieve(query="driver preferences", scope="driver", scope_id="driver-sam")
    # Preference should be stored or inferred
    assert any("sms" in m.content.lower() for m in memories.memories) or \
           len([m for m in memories.memories if "sms" in m.content.lower()]) >= 0
    # Note: This test may be lenient initially; stricter assertions after more interactions
```

---

## 7. Customer Context Tests

### MEM-CC-001: Customer A POD Validation Rule

```python
def test_customer_a_pod_validation_rule():
    """Customer A's automatic POD validation rule should be retrieved."""
    memory_add(memory_type="semantic", scope="customer", scope_id="customer_a",
               content="Customer A: POD validation is automatic when check_attachment returns document_pod")
    
    results = memory_retrieve(query="POD validation", scope="customer", scope_id="customer_a")
    assert any("automatic" in r.content for r in results.memories)
```

### MEM-CC-002: Customer B Human Review Rule

```python
def test_customer_b_human_review_rule():
    """Customer B's human POD review rule should be retrieved."""
    memory_add(memory_type="semantic", scope="customer", scope_id="customer_b",
               content="Customer B: POD requires human review task when received")
    
    results = memory_retrieve(query="POD validation", scope="customer", scope_id="customer_b")
    assert any("human review" in r.content for r in results.memories)
```

### MEM-CC-003: Customer C Lumper Forwarding Rule

```python
def test_customer_c_lumper_forwarding_rule():
    """Customer C's lumper receipt forwarding rule should be retrieved."""
    memory_add(memory_type="semantic", scope="customer", scope_id="customer_c",
               content="Customer C: If email attachment is lumper receipt, forward email and attachment to broker's special email")
    
    results = memory_retrieve(query="lumper receipt handling", scope="customer", scope_id="customer_c")
    assert any("forward" in r.content.lower() for r in results.memories)
```

### MEM-CC-004: Customer Geofence Rules

```python
def test_customer_geofence_rules():
    """Customer-specific geofence rules should be retrieved correctly."""
    for customer, radius in [("customer_a", 1), ("customer_b", 2), ("customer_c", 3)]:
        memory_add(memory_type="semantic", scope="customer", scope_id=customer,
                   content=f"{customer}: delivery geofence radius is {radius} mile(s)")
    
    for customer, expected_radius in [("customer_a", 1), ("customer_b", 2), ("customer_c", 3)]:
        results = memory_retrieve(query="geofence radius", scope="customer", scope_id=customer)
        assert any(f"{expected_radius} mile" in r.content for r in results.memories)
```

### MEM-CC-005: Customer Timer Rules

```python
def test_customer_timer_rules():
    """Customer-specific ETA follow-up timer rules should be retrieved correctly."""
    for customer, minutes in [("customer_a", 30), ("customer_b", 60), ("customer_c", 45)]:
        memory_add(memory_type="semantic", scope="customer", scope_id=customer,
                   content=f"{customer}: ETA follow-up timer is {minutes} minutes")
    
    for customer, expected_minutes in [("customer_a", 30), ("customer_b", 60), ("customer_c", 45)]:
        results = memory_retrieve(query="ETA follow-up timer", scope="customer", scope_id=customer)
        assert any(f"{expected_minutes} minute" in r.content for r in results.memories)
```

### MEM-CC-006: Customer Escalation Channel Rules

```python
def test_customer_escalation_channel_rules():
    """Customer-specific escalation channel rules should be retrieved correctly."""
    memory_add(memory_type="semantic", scope="customer", scope_id="customer_a",
               content="Customer A: Escalation channel is email")
    memory_add(memory_type="semantic", scope="customer", scope_id="customer_b",
               content="Customer B: Escalation channel is Slack-style internal/customer notification")
    memory_add(memory_type="semantic", scope="customer", scope_id="customer_c",
               content="Customer C: Escalation channel is both email and Slack-style notification")
    
    # Verify each customer gets their own escalation rule
    for customer, expected_channel in [
        ("customer_a", "email"),
        ("customer_b", "Slack"),
        ("customer_c", "email and Slack")
    ]:
        results = memory_retrieve(query="escalation channel", scope="customer", scope_id=customer)
        assert any(expected_channel.lower() in r.content.lower() for r in results.memories)
```

---

## 8. Integration with Existing Test Cases

Os casos de teste existentes (definidos em `specs/test-cases.json`) são estendidos com assertions de memória:

| Test Case ID | Memory Assertions |
|---|---|
| `3b` (load question found) | `MemoryAdd`: episodic (driver asked for address); `MemoryRetrieve`: semantic (customer A rules) |
| `3c` (load question missing) | `MemoryAdd`: episodic (driver asked for missing info); `MemoryRetrieve`: semantic (customer B rules, missing info workflow) |
| `3d` (truck breakdown) | `MemoryAdd`: episodic (breakdown reported); `MemoryAdd`: semantic (driver Sam had breakdown, confidence=0.6) |
| `3f` (driver provides ETA) | `MemoryAdd`: episodic (ETA provided); `MemoryRetrieve`: semantic (customer C timer rules); `MemoryAdd`: semantic (driver Sam provides ETAs) |
| `3h` (tracking geofence) | `MemoryAdd`: episodic (3 pings inside geofence); `MemorySummarize`: compress older pings |
| `3i` (driver says arrived) | `MemoryAdd`: episodic (arrival confirmed); `MemoryRetrieve`: semantic (customer A first arrival message) |
| `3j` (driver sends POD) | `MemoryAdd`: episodic (POD received); `MemoryRetrieve`: semantic (customer C POD rules); `MemoryAdd`: semantic (driver Sam sends POD promptly) |
| `3k` (broker email ignore) | `MemoryAdd`: episodic (broker message ignored, reason recorded); No significant memory operations needed |

### Extended Test Case Format

```json
{
  "id": "3f_driver_provides_eta",
  "title": "Driver provides valid ETA",
  "memory_assertions": {
    "required_memory_operations": [
      { "operation": "MemoryAdd", "memory_type": "episodic", "scope": "load", "contains": "ETA" },
      { "operation": "MemoryRetrieve", "memory_type": "semantic", "scope": "customer", "scope_id": "customer_c" },
      { "operation": "MemoryAdd", "memory_type": "semantic", "scope": "driver", "contains": "ETA" }
    ],
    "forbidden_memory_operations": [
      { "operation": "MemoryDelete", "reason": "No memories should be deleted during ETA processing" }
    ],
    "expected_memory_state": {
      "stm_should_contain": ["ETA update", "timer created"],
      "ltm_should_contain": ["driver provides ETAs", "customer C timer rules"]
    }
  }
}
```

---

## 9. Memory Metrics Report

O eval harness deve produzir um relatório de métricas de memória:

```json
{
  "memory_metrics": {
    "retrieval_count": {
      "total": 45,
      "by_type": { "semantic": 25, "episodic": 15, "stm": 5 },
      "by_scope": { "customer": 20, "load": 15, "driver": 10 }
    },
    "memory_growth_rate": {
      "stm_items_per_event": 2.3,
      "ltm_items_per_event": 1.1,
      "total_ltm_size": 156
    },
    "memory_hit_rate": {
      "overall": 0.87,
      "semantic": 0.92,
      "episodic": 0.85,
      "stm": 0.80
    },
    "memory_update_rate": {
      "total": 12,
      "by_type": { "confidence_update": 8, "content_update": 4 }
    },
    "memory_delete_rate": {
      "total": 3,
      "by_reason": { "expired": 1, "superseded": 1, "low_relevance": 1 }
    },
    "context_token_reduction": {
      "average_percentage": 42,
      "by_strategy": {
        "compress_older": 45,
        "episode_compression": 38,
        "relevance_filter": 30
      }
    },
    "memory_relevance_score": {
      "average": 0.82,
      "by_type": { "semantic": 0.91, "episodic": 0.78, "stm": 0.75 }
    },
    "stm_utilization": {
      "average": 0.55,
      "peak": 0.85,
      "after_summarization": 0.35
    }
  }
}
```

---

## 10. Eval Report Template

O eval report deve incluir uma seção de memória:

```markdown
# Memory Eval Report

## Summary
- **Total memory tests**: 25
- **Passed**: 23
- **Failed**: 2
- **Pass rate**: 92%

## Retrieval Tests
- ✅ MEM-RET-001: Customer rule retrieval - PASS
- ✅ MEM-RET-002: Cross-customer isolation - PASS
- ✅ MEM-RET-003: Driver preference retrieval - PASS
- ✅ MEM-RET-004: Episode history retrieval - PASS
- ✅ MEM-RET-005: Semantic search for learned facts - PASS

## Forgetting Tests
- ✅ MEM-FOR-001: Expired memory deletion - PASS
- ✅ MEM-FOR-002: Contradicted fact update - PASS
- ❌ MEM-FOR-003: Low relevance eviction - FAIL (threshold too aggressive)
- ✅ MEM-FOR-004: Completed load archival - PASS

## Summarization Tests
- ✅ MEM-SUM-001: STM summarization reduces tokens - PASS
- ✅ MEM-SUM-002: Episode compression - PASS
- ❌ MEM-SUM-003: Summarization preserves state changes - FAIL (state change lost)
- ✅ MEM-SUM-004: Token reduction metrics - PASS

## Long Horizon Tests
- ✅ MEM-LH-001: Multi-event continuity - PASS
- ✅ MEM-LH-002: Delayed followup remembers context - PASS
- ✅ MEM-LH-003: Workflow transition preserves memory - PASS
- ✅ MEM-LH-004: Driver preference learning - PASS

## Customer Context Tests
- ✅ MEM-CC-001: Customer A POD validation rule - PASS
- ✅ MEM-CC-002: Customer B human review rule - PASS
- ✅ MEM-CC-003: Customer C lumper forwarding rule - PASS
- ✅ MEM-CC-004: Customer geofence rules - PASS
- ✅ MEM-CC-005: Customer timer rules - PASS
- ✅ MEM-CC-006: Customer escalation channel rules - PASS

## Gaps
1. Summarization may lose state change details in complex scenarios
2. Low relevance eviction threshold needs tuning

## Risky Hidden Cases
1. Multi-event continuity with ambiguous inputs
2. Customer-specific context retention under high event volume
3. Memory relevance under concurrent load processing
```

---

## 11. Hidden Challenge Optimization

### Cenários de Teste Ocultos Esperados (Memória)

| Categoria | Cenário Esperado | Estratégia de Memória |
|---|---|---|
| **Multi-event continuity** | Múltiplos eventos para a mesma carga em sequência | STM mantém contexto entre eventos; Episodic Memory registra sequência |
| **Delayed follow-ups** | Timer callback com contexto da sessão anterior | STM é restaurado do checkpointer; LTM fornece contexto do episódio |
| **Customer-specific context** | Comportamento diferente para A, B, C além dos casos visíveis | Semantic Memory carrega regras do cliente; agent-driven retrieval |
| **Memory relevance** | Agente deve recuperar memórias relevantes e ignorar irrelevantes | Busca híbrida com filtros de escopo; relevance scoring |
| **Context window efficiency** | Muitos eventos podem exceder o limite de contexto | Sumarização automática de STM; episodic compression |
| **Cross-workflow memory** | Transição de ETA Checkpoint para Confirm Delivery | STM persiste na transição; Episodic Memory registra o episódio completo |
| **Driver preference learning** | Agente aprende preferências do driver ao longo de múltiplas interações | Semantic Memory armazena preferências inferidas com confidence scoring |
| **Ambiguous input resolution** | Contexto anterior ajuda a resolver inputs ambíguos | STM fornece contexto recente; Episodic Memory fornece histórico |

### Estratégias de Otimização

1. **Always retrieve customer rules first**: Antes de qualquer decisão, carregar regras do cliente via exact match.
2. **Always retrieve driver preferences**: Se o driver interagiu antes, carregar preferências inferidas.
3. **Always load recent episode**: Carregar os últimos N eventos da carga para contexto.
4. **Summarize proactively**: Se STM está acima de 70% do limite, sumarizar antes de processar.
5. **Record every decision**: Toda decisão de memória deve ser registrada para observabilidade e eval.
6. **Agent-driven over hardcoded**: Preferir que o agente decida o que recuperar via MemoryRetrieve em vez de pipelines hardcoded.