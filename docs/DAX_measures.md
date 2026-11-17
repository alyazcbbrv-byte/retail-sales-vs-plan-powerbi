# DAX ölçüləri

Bütün ölçülər `_Ölçülər` cədvəlindədir və Data panelində qovluqlara bölünüb.

## 1 · Satış və Plan

### Satış

Seçimdəki satışların cəmi

```dax
Satış = SUM ( fact_sales[Satış] )
```

### Plan

Seçimdəki planın cəmi. Diqqət: plan satışın 29 gün gecikmiş nüsxəsidir

```dax
Plan = SUM ( fact_plan[Plan] )
```

### Plan icrası %

Satış / Plan

```dax
Plan icrası % = DIVIDE ( [Satış], [Plan] )
```

### Plan fərqi

Satış - Plan

```dax
Plan fərqi = [Satış] - [Plan]
```

### Satış payı %

Seçimdəki cəmə görə pay

```dax
Satış payı % = DIVIDE ( [Satış], CALCULATE ( [Satış], ALLSELECTED () ) )
```

### Orta gündəlik satış

Bir mağazanın bir gündəki orta satışı

```dax
Orta gündəlik satış = DIVIDE ( [Satış], COUNTROWS ( fact_sales ) )
```

## 2 · Müqayisə (zaman)

### Cari il satışı

Seçimdəki son ilin satışı

```dax
Cari il satışı = VAR y = YEAR ( CALCULATE ( MAX ( fact_sales[Tarix] ) ) ) RETURN CALCULATE ( [Satış], FILTER ( VALUES ( 'Calendar'[Date] ), YEAR ( 'Calendar'[Date] ) = y ) )
```

### Ötən ilin eyni dövrü satışı

Bir il əvvəlki eyni dövr

```dax
Ötən ilin eyni dövrü satışı = VAR y = YEAR ( CALCULATE ( MAX ( fact_sales[Tarix] ) ) ) RETURN CALCULATE ( [Satış], SAMEPERIODLASTYEAR ( FILTER ( VALUES ( 'Calendar'[Date] ), YEAR ( 'Calendar'[Date] ) = y ) ), REMOVEFILTERS ( 'Calendar' ) )
```

### İldən ilə artım %

Like-for-like illik artım

```dax
İldən ilə artım % = DIVIDE ( [Cari il satışı] - [Ötən ilin eyni dövrü satışı], [Ötən ilin eyni dövrü satışı] )
```

### Cari ay satışı

Seçimdəki son ayın satışı

```dax
Cari ay satışı = VAR d = CALCULATE ( MAX ( fact_sales[Tarix] ) ) RETURN CALCULATE ( [Satış], DATESBETWEEN ( 'Calendar'[Date], EOMONTH ( d, -1 ) + 1, EOMONTH ( d, 0 ) ), REMOVEFILTERS ( 'Calendar' ) )
```

### Ötən ay satışı

Son aydan əvvəlki ayın satışı

```dax
Ötən ay satışı = VAR d = CALCULATE ( MAX ( fact_sales[Tarix] ) ) RETURN CALCULATE ( [Satış], DATESBETWEEN ( 'Calendar'[Date], EOMONTH ( d, -2 ) + 1, EOMONTH ( d, -1 ) ), REMOVEFILTERS ( 'Calendar' ) )
```

### Aylıq artım %

Ay-ay artım

```dax
Aylıq artım % = DIVIDE ( [Cari ay satışı] - [Ötən ay satışı], [Ötən ay satışı] )
```

### İlin əvvəlindən satış (YTD)

YTD

```dax
İlin əvvəlindən satış (YTD) = TOTALYTD ( [Satış], 'Calendar'[Date] )
```

## 3 · Mağaza şəbəkəsi

### Aktiv mağaza sayı

Seçimdə satışı olan unikal mağaza sayı

```dax
Aktiv mağaza sayı = DISTINCTCOUNT ( fact_sales[Mağaza_Kodu] )
```

### Mağaza başına satış

Satış / aktiv mağaza

```dax
Mağaza başına satış = FORMAT ( DIVIDE ( [Satış], [Aktiv mağaza sayı] ) / 1000000, "0.00" ) & " M"
```

### Mağaza sayı

Mağaza cədvəlindəki sətirlər (dövrdən asılı deyil)

```dax
Mağaza sayı = COUNTROWS ( dim_store )
```

## 4 · Churn analizi

### Hazırda aktiv mağaza

Son satışı 2025-09-01-dən sonra olan mağazalar

```dax
Hazırda aktiv mağaza = CALCULATE ( COUNTROWS ( dim_store ), dim_store[Status] = "Aktiv" )
```

### Bağlanmış mağaza (cəmi)

Satışı dayanmış mağazalar

```dax
Bağlanmış mağaza (cəmi) = CALCULATE ( COUNTROWS ( dim_store ), dim_store[Status] = "Bağlanıb" )
```

### Açılan mağaza

Dövr ərzində ilk satışı olan mağaza

```dax
Açılan mağaza = VAR a = MIN ( 'Calendar'[Date] ) VAR b = MAX ( 'Calendar'[Date] ) RETURN COUNTROWS ( FILTER ( dim_store, dim_store[İlk satış] >= a && dim_store[İlk satış] <= b ) )
```

### Bağlanan mağaza

Dövr ərzində satışı dayanan mağaza (2025-09-dan sonra müşahidə tamamlanmayıb)

```dax
Bağlanan mağaza = VAR a = MIN ( 'Calendar'[Date] ) VAR e = MIN ( MAX ( 'Calendar'[Date] ), DATE ( 2025, 8, 31 ) ) RETURN IF ( a > DATE ( 2025, 8, 31 ), BLANK (), COUNTROWS ( FILTER ( dim_store, dim_store[Son satış] >= a && dim_store[Son satış] <= e && dim_store[Status] = "Bağlanıb" ) ) )
```

### Dövrün əvvəlində aktiv mağaza

Churn bazası

```dax
Dövrün əvvəlində aktiv mağaza = VAR a = MIN ( 'Calendar'[Date] ) RETURN COUNTROWS ( FILTER ( dim_store, dim_store[İlk satış] < a && dim_store[Son satış] >= a ) )
```

### Churn %

Bağlanan / dövrün əvvəlində aktiv

```dax
Churn % = DIVIDE ( [Bağlanan mağaza], [Dövrün əvvəlində aktiv mağaza] )
```

### Orta aylıq churn %

Aylıq churn faizlərinin ortası

```dax
Orta aylıq churn % = AVERAGEX ( VALUES ( 'Calendar'[İlAy] ), [Churn %] )
```

### Orta mağaza ömrü (gün)

Bağlanmış mağazaların ilk və son satışı arasındakı gün

```dax
Orta mağaza ömrü (gün) = AVERAGEX ( FILTER ( dim_store, dim_store[Status] = "Bağlanıb" ), DATEDIFF ( dim_store[İlk satış], dim_store[Son satış], DAY ) + 1 )
```

### Bağlanmışların satış payı %

Tarixi satışın neçə faizi sonradan bağlanan mağazalardan gəlir

```dax
Bağlanmışların satış payı % = DIVIDE ( CALCULATE ( [Satış], dim_store[Status] = "Bağlanıb" ), [Satış] )
```
