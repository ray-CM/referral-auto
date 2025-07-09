# Oracle NetSuite ERP API Spec (Referral Report)

## Invoice Payment Status API

Retrieve the invoice payment status corresponding to each billing account ID.

### Request

#### Query Parameters
| Parameter | Type | Mandatory | Description |
|-----------|------|-----------|-------------|
| month | String | Yes | Invoice month. Format: `YYYYMM`. |
| billing_account_ids | String | Yes | A comma-separated list of billing account IDs (e.g., `AAAAAA-AAAAAA-AAAAAA,BBBBBB-BBBBBB-BBBBBB`). |

### Response

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| data | Array | A list of invoice data objects. |

##### Invoice Data Object Fields

| Field | Type | Description |
|-------|------|-------------|
| invoice_number | String | The invoice number. |
| invoice_date | String | The invoice issue date. |
| payment_status | String | Current payment status of the invoice. |
| items | Array | List of billing account IDs included in the invoice. |

#### Example Response

```json
{
  "data": [
    {
      "invoice_number": "IV-HK2025010000001",
      "invoice_date": "2025/01/03",
      "payment_status": "Open",
      "items": [
        "AAAAAA-AAAAAA-AAAAAA",
        "BBBBBB-BBBBBB-BBBBBB"
      ]
    },
    ...
  ]
}
```
