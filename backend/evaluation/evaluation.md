# Classifier Evaluation

20 manually labeled tickets, run against the live classifier (`app/services/router_service.route_ticket`, GPT-4.1 via OpenAI Structured Outputs). Expected labels were fixed in `labeled_tickets.py` before this evaluation ran.

- **Overall accuracy (category + priority + team all correct): 95.0%**
- Category accuracy: 100.0%
- Priority accuracy: 95.0%
- Team accuracy: 100.0%

| # | Ticket | Expected Category | Expected Priority | Expected Team | AI Prediction | Correct |
|---|---|---|---|---|---|---|
| 1 | I was charged three times for my subscription this month, please re... | Billing | High | Finance | Billing / High / Finance | ✓ |
| 2 | My invoice shows the wrong amount, can someone check my last payment? | Billing | Medium | Finance | Billing / High / Finance | ✗ |
| 3 | Do you offer any discount if I switch to the annual plan? | Sales | Low | Sales | Sales / Low / Sales | ✓ |
| 4 | Our production system is down and customers can't check out. This i... | Technical | High | Engineering | Technical / High / Engineering | ✓ |
| 5 | The app crashes every time I try to upload a profile picture. | Technical | Medium | Engineering | Technical / Medium / Engineering | ✓ |
| 6 | I forgot my password and the reset email never arrived. | Technical | Medium | Engineering | Technical / Medium / Engineering | ✓ |
| 7 | Our office WiFi keeps disconnecting every few minutes, the VPN is u... | Network | High | Network Operations | Network / High / Network Operations | ✓ |
| 8 | I can't connect to the company VPN from home today. | Network | Medium | Network Operations | Network / Medium / Network Operations | ✓ |
| 9 | The firewall seems to be blocking our API calls to your service. | Network | Medium | Network Operations | Network / Medium / Network Operations | ✓ |
| 10 | Can I get a demo of the enterprise plan for my team of 50 people? | Sales | Low | Sales | Sales / Low / Sales | ✓ |
| 11 | What's the pricing difference between the Pro and Business tiers? | Sales | Low | Sales | Sales / Low / Sales | ✓ |
| 12 | We're interested in upgrading, please send a quotation. | Sales | Low | Sales | Sales / Low / Sales | ✓ |
| 13 | Just wanted to say the new update looks great, nice work! | General | Low | Support | General / Low / Support | ✓ |
| 14 | Do you have a dark mode planned for the mobile app? | General | Low | Support | General / Low / Support | ✓ |
| 15 | Where can I find your API documentation? | General | Low | Support | General / Low / Support | ✓ |
| 16 | THIS IS RIDICULOUS!!! I've emailed THREE TIMES about my account bei... | Technical | High | Engineering | Technical / High / Engineering | ✓ |
| 17 | Help | General | Low | Support | General / Low / Support | ✓ |
| 18 | Not working | General | Low | Support | General / Low / Support | ✓ |
| 19 | Something is wrong with my account, please check. | General | Low | Support | General / Low / Support | ✓ |
| 20 | It failed again, not sure why. | General | Low | Support | General / Low / Support | ✓ |

## Confidence calibration

The model self-reports a `confidence` score (0-100) with every prediction. Self-reported LLM confidence is not automatically trustworthy — it's only useful if it actually tracks correctness. Checking that is a real evaluation, not just displaying the number:

- Average confidence on **correct** predictions: 92.2
- Average confidence on **incorrect** predictions: 95.0
- Confidence was **not** lower on the misses in this run — the self-reported score should not be treated as a reliable correctness signal without a larger evaluation set.

Accuracy by confidence band (a single average can hide a band that's badly miscalibrated -- this checks whether accuracy actually increases band over band, not just on average):

| Confidence band | Tickets | Accuracy |
|---|---|---|
| 90-100 | 17 | 94.1% |
| 70-89 | 2 | 100.0% |
| below 70 | 1 | 100.0% |

## Notes on ambiguous cases

Tickets 16-20 are the mission's 3 required edge cases (angry tone, very short message, ambiguous ticket). Tickets 19-20 in particular are genuinely underspecified by design -- a different, equally defensible category could be argued. See the `note` field in `labeled_tickets.py` for the reasoning behind every expected label.
