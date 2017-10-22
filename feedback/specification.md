Project Specification Feedback
==================

Commit graded: 24839970cbea4963e90ab8d22facea323b25cd18

### The product backlog (10/10)

10:  Product backlog is generally complete and adequate. The backlog looks good. However, you have scheduled multiple additional features starting from sprint 2. Please make sure you fully implement the game part before moving to those functions.

### Data models (9/10)

9:  Models are generally complete but there are several problems. First, in your room model, players is a ManyToManyField. However, one user cannot be in multiple room at the same time. Also the player_cards in Game model is a CharField, how would you identify a specific user's card with a CharField? Spliting and reconstruct a string might be complicated.

### Wireframes or mock-ups (10/10)

10: Wireframes are generally complete and adequate. 

### Additional Information

This poker game requires a lot of websockets technologies. However, in your specifiction you did not describe this part. Think through the whole process before you start to code. In order to success, please focusing on your basic game function. Do not spend time on your addictional features until you have finished your basic game function. And your credit function is unnecessery. 

---
#### Total score (/30)
---
Graded by: Sheng Qian (sqian@andrew.cmu.edu)

To view this file with formatting, visit the following page: https://github.com/CMU-Web-Application-Development/<TEAM_NUMBER>/blob/master/feedback/specification-feedback.md
