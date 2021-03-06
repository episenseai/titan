from jose import jwk, jwt, JOSEError
from jose.utils import base64url_decode, base64url_encode
from devtools import debug
import base64

jwt_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImU4NzMyZGIwNjI4NzUxNTU1NjIxM2I4MGFjYmNmZDA4Y2ZiMzAyYTkiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiI0ODM5OTI5NTkwNzctY2R0c2o0OGRobnQ4N21qbGJuNmpsdDcwN2xzMnN0MnAuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiI0ODM5OTI5NTkwNzctY2R0c2o0OGRobnQ4N21qbGJuNmpsdDcwN2xzMnN0MnAuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMTcxNzkzMjkxMDk3ODY5MDk2MDUiLCJlbWFpbCI6InN1c2hhbnQubWl0aGlsYTg5QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhdF9oYXNoIjoiS0lnNE9pTVktaTFPaHdVc0ZBUTBQZyIsIm5vbmNlIjoieDIzUGw2ZVBSM21CNmVqOGVGcWNET3hQbTd0ZXFoQzZSUGxnVFdOSEVuSHRJSlBTIiwibmFtZSI6IlN1c2hhbnQgS3VtYXIiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EtL0FPaDE0R2haM3NWUjZKd3p4NlVtUC15dFlHWW9rLURsUTdCeTlvQ3JHei1hcUE9czk2LWMiLCJnaXZlbl9uYW1lIjoiU3VzaGFudCIsImZhbWlseV9uYW1lIjoiS3VtYXIiLCJsb2NhbGUiOiJlbiIsImlhdCI6MTYxNDk4NTM5NSwiZXhwIjoxNjE0OTg4OTk1fQ.c-FrOsHbJVNIfmLD4hyHLvPGNxfx_TPgSyDXPN4NpEHAoR8Ag9cNFlYbNAh4ofyeKSyKtWMmWhK_DyK4Ia7duVwDxl8Zn2Ar9gtZxb4I_TrJqbzldZv0TJp9wQWewBZ9T6U8SIqEI3S5ikkMjkbtPjQsi9b-YbPntmDJWKOeZcd5dcbEaLBnFLyJEl8yeSnvfzupTZsrSUQXqqSwj-G93ckk2y2oC_qOCIix93hEiTxnApwAGzcHxeZutnd28tS-86ptV3Iwu8cyzcMfz1-WqZ8ZB9YGCCEcZ-3Oh63nHknwzU0KadfX6zxmiTeLpueE8mIMSNv0_eHMSCrVby_cxw"
gkeys = {
    "keys": [
        {
            "alg": "RS256",
            "kid": "fed80fec56db99233d4b4f60fbafdbaeb9186c73",
            "n": "qvBBLhUa94lyP6KktX8SGtf6RVnv6bV76GlPG5YBOxHmm_qBYUIyKtX1RLL9OYh_ZeKOnfwEhHEY3IBZfwZqV0TPtS4qv7-nP0d_EoJ4f2-sM98EwcvHOT2MY_70JMqHcJ235Tf_jYARnS3saFETAJl1K34JmBoS3zOAjq56n2Iq4KNfsBoRdmlT7eQc-B8xAj2-i0-bu1EPSFqfU_h-nOynEJQPr8Cp9WX_m2XR_7Kk8hudm0hemRiunnGbgd6QNiohchPRu_fI1NOfeDeoazmnmWO2wreZ00CkiDEVnAS_Kzwj1a7JU7gqY69Skxe82-TkHOW3AfNwOtQzxxvscw",
            "use": "sig",
            "e": "AQAB",
            "kty": "RSA",
        },
        {
            "kid": "e8732db06287515556213b80acbcfd08cfb302a9",
            "alg": "RS256",
            "kty": "RSA",
            "use": "sig",
            "n": "4RIrO30287Wsq3gqXCMkUYMVAeI3H8LVE6IXR1krdFeGnZLiGUPwcbkeVpXf3lmJdsStOg-jijces2DZCfPyIBiQuLYfxxmAZE6ErJ0QJFg1stwli2Pz9ncYhFoqi8pXr7kEzEJBTzX4thuw56ydbGsshSEznPXoerCJOc7UI2-n0wFCWQ4YLHbh_PrWt4vdadyUUUW_QpQHXQLdD8q_Qwqdj0O9zlJE7R6Elw2E9EqnHyIGu1hmLxhqrTru1M18SUhONYbVskV_BCEdVKs__X96849HorWQDCAgVMWfGsdMVq55FAdJ680N5UmQDRynIZ4-PeNGN4S9iw2mbMNEBQ",
            "e": "AQAB",
        },
    ]
}


success = False
keys = gkeys["keys"]
for k in keys:
    try:
        data = jwt.decode(jwt_token, k)
        debug(data)
        success = True
        break
    except JOSEError as exc:
        print("*****\n", exc)
        pass
