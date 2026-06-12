# Refurbishment Unit-Cost Report

Generated: 2026-06-12T10:37:41+00:00

Model version: `refurbishment_unit_cost_v0.1`

## Plain Result

This report applies unit-cost factors to the quantified refurbishment work-scope table.

If the status is `blocked_missing_unit_costs`, the model has quantities but the private unit-cost CSV still needs rates.

## Summary

| Scenario | Status | Base cost | Factors used | Missing | Missing drivers |
| --- | --- | --- | --- | --- | --- |
| goldeneye_dissertation | blocked_missing_unit_costs | $0 | 0 | 9 | cleaning_drying_per_km; compatibility_review_each; engineering_study_each; fracture_decompression_study_each; imr_plan_each; inspection_per_km; material_testing_campaign; replacement_steel_kg; wall_thickness_verification_per_km |
| goldeneye_poster | blocked_missing_unit_costs | $0 | 0 | 9 | cleaning_drying_per_km; compatibility_review_each; engineering_study_each; fracture_decompression_study_each; imr_plan_each; inspection_per_km; material_testing_campaign; replacement_steel_kg; wall_thickness_verification_per_km |

## Input Files

- Work scope: `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/06_screening_and_decision/refurbishment_work_scope_goldeneye_benchmark.csv`
- Unit costs: `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/04_cost_economics/private/refurbishment_unit_costs_private.csv`

## Output Files

- Row costs: `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/04_cost_economics/refurbishment_costs_goldeneye_benchmark.csv`
- Summary: `C:/Users/aj52/Documents/Repurposing Pipelines/model_layers/04_cost_economics/refurbishment_cost_summary_goldeneye_benchmark.csv`

## Important Caveat

Public GitHub files must not contain confidential contractor rates, commercial estimates, or restricted cost data. Fill the private unit-cost CSV locally, then rerun the command.
