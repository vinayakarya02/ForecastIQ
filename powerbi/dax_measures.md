# ForecastIQ — DAX Measures

Copy into a dedicated `_Measures` table in Power BI. Names match the visuals in the dashboard design.

## Core measures
```DAX
Total Revenue = SUM ( fact_sales[sales] )

Total Profit = SUM ( fact_sales[profit] )

Total Units = SUM ( fact_sales[quantity] )

Order Count = DISTINCTCOUNT ( fact_sales[order_id] )

Profit Margin % =
DIVIDE ( [Total Profit], [Total Revenue] )

Avg Order Value =
DIVIDE ( [Total Revenue], [Order Count] )
```

## Time intelligence (requires dim_date marked as date table)
```DAX
Revenue MoM % =
VAR Curr = [Total Revenue]
VAR Prev =
    CALCULATE ( [Total Revenue], DATEADD ( dim_date[full_date], -1, MONTH ) )
RETURN DIVIDE ( Curr - Prev, Prev )

Revenue YoY % =
VAR Curr = [Total Revenue]
VAR Prev =
    CALCULATE ( [Total Revenue], DATEADD ( dim_date[full_date], -1, YEAR ) )
RETURN DIVIDE ( Curr - Prev, Prev )

Revenue 3M Avg =
AVERAGEX (
    DATESINPERIOD ( dim_date[full_date], MAX ( dim_date[full_date] ), -3, MONTH ),
    [Total Revenue]
)
```

## Forecast measures (from forecast_results)
```DAX
Actual Revenue =
CALCULATE ( SUM ( forecast_results[yhat] ), forecast_results[is_actual] = 1 )

Forecast Revenue =
CALCULATE ( SUM ( forecast_results[yhat] ), forecast_results[is_actual] = 0 )

Forecast Lower =
CALCULATE ( SUM ( forecast_results[yhat_lower] ), forecast_results[is_actual] = 0 )

Forecast Upper =
CALCULATE ( SUM ( forecast_results[yhat_upper] ), forecast_results[is_actual] = 0 )

Best Model MAPE =
CALCULATE ( MIN ( model_metrics[mape] ), model_metrics[is_best] = 1 )
```

## RFM (from vw_customer_rfm imported as a table)
```DAX
Customer Count = DISTINCTCOUNT ( vw_customer_rfm[customer_id] )

Avg Monetary = AVERAGE ( vw_customer_rfm[monetary] )
```
