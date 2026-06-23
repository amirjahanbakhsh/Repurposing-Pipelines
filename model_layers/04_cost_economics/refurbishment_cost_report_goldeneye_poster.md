# Refurbishment Unit-Cost Report

Generated: 2026-06-14T22:03:15+00:00

Model version: `refurbishment_unit_cost_v0.2`

## Plain Result

This report applies unit-cost factors to the quantified refurbishment work-scope table.

If the status is `screening_result`, public screening defaults were used. This is useful for comparing cases, but it is not a contractor estimate.

If the status is `blocked_missing_unit_costs`, the model has quantities but the chosen unit-cost CSV still needs rates.

## Summary

| Scenario | Status | Base cost | Factors used | Missing | Missing drivers |
| --- | --- | --- | --- | --- | --- |
| goldeneye_poster | screening_result | $15,453,154 | 10 | 0 | none |

## Input Files

- Work scope: `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/06_screening_and_decision/refurbishment_work_scope_goldeneye_poster.csv`
- Unit costs: `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/04_cost_economics/refurbishment_unit_cost_screening_defaults.csv`

## Output Files

- Row costs: `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/04_cost_economics/refurbishment_costs_goldeneye_poster.csv`
- Summary: `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/04_cost_economics/refurbishment_cost_summary_goldeneye_poster.csv`

## Important Caveat

Public GitHub files must not contain confidential contractor rates, commercial estimates, or restricted cost data. Use public screening defaults for early ranking, then replace them with private project estimates before making publishable cost claims.
