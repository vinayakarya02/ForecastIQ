"""Analytics layer over the warehouse.

Modules: kpis, trends, segmentation (RFM/CLV), products, regional, returns, and a
rule-based insights engine. Every function takes a SQLAlchemy engine and returns a
DataFrame or dict; metric definitions are shared via SQL views.
"""
