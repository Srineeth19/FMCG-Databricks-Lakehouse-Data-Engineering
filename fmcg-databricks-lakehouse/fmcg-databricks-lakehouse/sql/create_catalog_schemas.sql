-- create_catalog_schemas.sql
-- Run in a Databricks SQL Editor / SQL Warehouse if you prefer SQL over
-- notebook 00_setup_catalog_schema.py

CREATE CATALOG IF NOT EXISTS fmcg_lakehouse;
USE CATALOG fmcg_lakehouse;

CREATE SCHEMA IF NOT EXISTS bronze COMMENT 'Raw, as-landed data from S3 for both source companies.';
CREATE SCHEMA IF NOT EXISTS silver COMMENT 'Cleaned, conformed, deduplicated dimensions and facts.';
CREATE SCHEMA IF NOT EXISTS gold   COMMENT 'Business-ready denormalized and aggregate tables for BI/Genie.';

CREATE VOLUME IF NOT EXISTS bronze.raw_files;
