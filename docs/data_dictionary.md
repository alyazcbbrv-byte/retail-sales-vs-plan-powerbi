# Data lüğəti

Mənbə: mağaza şəbəkəsinin gündəlik satış və plan faylları (`Mağaza Satış.xlsx`, `Mağaza Planı.xlsx`). Fayllar repo-ya daxil deyil, ETL nəticəsi `data/processed/` qovluğundadır. Pul vahidi datada göstərilməyib.

## fact_sales (113 829 sətir)

| Sütun | Tip | Təsvir |
|---|---|---|
| `Mağaza_Kodu` | mətn | Mağazanın unikal kodu (məsələn `422.A`) |
| `Tarix` | tarix | Satış günü |
| `Satış` | rəqəm | Mağazanın həmin gündəki satışı |

Qranulyarlıq: 1 sətir = 1 mağaza × 1 gün. Dublikat, boş və mənfi dəyər yoxdur.

## fact_plan (113 915 sətir)

| Sütun | Tip | Təsvir |
|---|---|---|
| `Mağaza_Kodu` | mətn | Mağaza kodu |
| `Tarix` | tarix | Plan günü |
| `Plan` | rəqəm | Mağaza üçün həmin günün planı |

## dim_store (274 mağaza)

| Sütun | Təsvir |
|---|---|
| `Mağaza_Kodu`, `Mağaza_adı` | Açar və ad (1:1) |
| `Region` | Mağaza adından çıxarılıb (`Abşeron 5` → `Abşeron`), 50 region |
| `Region_qrupu` | `Bakı və Abşeron` və ya `Rayonlar` |
| `Mağaza_nömrəsi` | Adın sonundakı nömrə |
| `Açılış_ili`, `İlk_satış`, `Son_satış` | İlk və son satış tarixinə görə |
| `Satış_günü` | Satış olan günlərin sayı |
| `Orta_günlük_satış` | Mağazanın orta günlük satışı |
| `Ölçü_qrupu` | Orta günlük satışa görə üçdə bir: Kiçik, Orta, Böyük |
| `Status` | `Aktiv` (son satış 2025-09-01-dən sonra) və ya `Bağlanıb` |

## Təmizləmə qaydaları (`src/etl.py`)

- Yalnız əsas vərəqlər oxunur (`Mağaza Satış 2`, `Mağaza Plan`). `Sheet4` vərəqləri iş hesablamalarıdır.
- Tarix və rəqəm sütunları tiplərə çevrilir, kod və adlar təmizlənir.
- Yoxlamalar: kod ilə ad 1:1, mağaza-gün dublikatı yoxdur, satış > 0, plandakı hər mağaza satışda var.

## Analiz pəncərəsi (Power BI)

Hesabat **2022-01-01 – 2025-09-30** arasını əhatə edir:

- 2021 (yalnız 11 mağaza, cəmi satışın 0.4%) çıxarılıb.
- 2025-10 çıxarılıb: satış yalnız 1 gün üçün var, plan isə bütün ay üçün.
