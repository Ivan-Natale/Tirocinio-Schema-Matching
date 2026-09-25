## Esperimento con più soglie

Dopo il primo esperimento con soglia 0.50, la baseline è stata
eseguita utilizzando cinque soglie diverse:

- 0.20
- 0.30
- 0.33
- 0.50
- 0.70

I risultati ottenuti sono:

| Soglia | TP | FP | FN | Precision | Recall | F1-score |
|-------:|---:|---:|---:|----------:|-------:|---------:|
| 0.20 | 6 | 6 | 1 | 0.5000 | 0.8571 | 0.6316 |
| 0.30 | 6 | 3 | 1 | 0.6667 | 0.8571 | 0.7500 |
| 0.33 | 6 | 3 | 1 | 0.6667 | 0.8571 | 0.7500 |
| 0.50 | 2 | 0 | 5 | 1.0000 | 0.2857 | 0.4444 |
| 0.70 | 0 | 0 | 7 | 0.0000 | 0.0000 | 0.0000 |

### Osservazione personale sulla soglia 0.33

Ho ritenuto particolarmente interessante la soglia 0.33 perché
permette di recuperare diverse corrispondenze che condividono una
sola parola significativa.

Ad esempio:

- `first_name` e `given_name`
- `last_name` e `family_name`
- `postal_code` e `zip_code`
- `total_spent` e `total_amount`

Con questa soglia la recall passa da 0.2857, ottenuta con soglia 0.50,
a 0.8571.

Allo stesso tempo ,purtroppo, vengono introdotti tre falsi positivi:

- `first_name` e `family_name`
- `last_name` e `given_name`
- `postal_code` e `client_code`

Questo mostra che abbassare la soglia permette di recuperare più
corrispondenze, ma aumenta anche il rischio di accettare coppie
lessicalmente simili ma semanticamente differenti.

La coppia `customer_id` e `client_code` continua invece a non essere
riconosciuta, poiché la similarità di Jaccard tra i due nomi è pari a 0.