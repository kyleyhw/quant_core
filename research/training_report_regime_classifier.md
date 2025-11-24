# XGBoost Regime Classifier - Training Report

**Date**: 2025-11-24 19:41:13

**Symbol**: CSV: data/SPY_1hour_1year.csv

**Period**: 2015-01-01 to 2023-12-31


## 1. Data Loading

Loaded **2543** rows of data


**Sample Data:**

| date                      |   open |   high |    low |   close |           volume |
|:--------------------------|-------:|-------:|-------:|--------:|-----------------:|
| 2024-06-11 09:30:00-04:00 | 534.1  | 534.1  | 532.05 |  532.76 | 741817           |
| 2024-06-11 10:00:00-04:00 | 532.76 | 534.71 | 532.59 |  534.64 | 476843           |
| 2024-06-11 11:00:00-04:00 | 534.71 | 534.76 | 533.68 |  533.84 | 483994           |
| 2024-06-11 12:00:00-04:00 | 533.84 | 534.26 | 533.55 |  534.1  | 275434           |
| 2024-06-11 13:00:00-04:00 | 534.12 | 535.24 | 533.73 |  535.2  | 368683           |
| 2024-06-11 14:00:00-04:00 | 535.13 | 536.64 | 534.95 |  536.2  | 652528           |
| 2024-06-11 15:00:00-04:00 | 536.2  | 537.01 | 535.62 |  536.91 |      1.73731e+06 |
| 2024-06-12 09:30:00-04:00 | 541.62 | 542.96 | 541.21 |  542.67 |      1.19641e+06 |
| 2024-06-12 10:00:00-04:00 | 542.68 | 543.95 | 542.55 |  543.09 |      1.05491e+06 |
| 2024-06-12 11:00:00-04:00 | 543.08 | 543.4  | 542.53 |  543    | 608173           |

## 2. Feature Engineering

Calculated **20** features

Data after dropping NaN: **2344** rows


## 3. Regime Labeling

**Regime Distribution:**

- Bull (0): 1011 samples (43.5%)

- Bear (1): 641 samples (27.6%)

- Sideways (2): 672 samples (28.9%)


**Selected Features (13):**

```text
SMA_50, SMA_200, EMA_20, MACD_12_26_9, MACDS_12_26_9, MACDH_12_26_9, RSI_14, STOCHk_14_3_3, STOCHd_14_3_3, BBL_20_2.0...
```

## 4. Train/Val/Test Split

- **Train**: 1394 samples (60%)

- **Validation**: 464 samples (20%)

- **Test**: 466 samples (20%)


## 5. Model Training

**Metrics:**

- Best Iteration: `0`

- Best Validation Loss: `1.0896`



## 6. Model Evaluation

**Classification Report:**


|              |   precision |   recall |   f1-score |    support |
|:-------------|------------:|---------:|-----------:|-----------:|
| Bull         |   0         | 0        |   0        | 186        |
| Bear         |   0.276824  | 1        |   0.433613 | 129        |
| Sideways     |   0         | 0        |   0        | 151        |
| accuracy     |   0.276824  | 0.276824 |   0.276824 |   0.276824 |
| macro avg    |   0.0922747 | 0.333333 |   0.144538 | 466        |
| weighted avg |   0.0766315 | 0.276824 |   0.120035 | 466        |


**Confusion Matrix:**

![Confusion Matrix](C:\Users\Kyle\PycharmProjects\ibkr_quant_core\models\regime_confusion_matrix.png)



**Feature Importance:**

![Top 15 Features](C:\Users\Kyle\PycharmProjects\ibkr_quant_core\models\regime_feature_importance.png)


## 7. Model Persistence

✓ Model saved to `models/xgb_regime_classifier.json`

✓ Confusion matrix saved to `models\regime_confusion_matrix.png`

✓ Feature importance saved to `models\regime_feature_importance.png`

---

*Report generated in 0.85 seconds*
