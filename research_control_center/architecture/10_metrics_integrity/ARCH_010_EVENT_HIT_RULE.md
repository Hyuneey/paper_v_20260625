# Event Hit Rule

An attack-event unit is detected when at least one alarm episode has non-empty half-open overlap with it:

```text
hit(event) = any(alarm.start < event.end and event.start < alarm.end)
```

There is no minimum overlap duration, pre/post grace window, delay allowance, label dilation, or point adjustment. The frozen metric is therefore **PA-FREE**. Boundary touch without shared row is not overlap. One long alarm episode could theoretically overlap more than one attack unit; the implementation does not enforce one-to-one matching.

Recall uses the event-unit detection vector, not point recall and not episode precision.
