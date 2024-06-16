# Kicktipp-Bot

This script can automatically enter tips into Kicktipp based on the quotes of the bookmakers and xG data. It is written in Python and uses Selenium to interact with the website.

## Easy Up & Running

Before you can launch the script, you need to put your Kicktipp credentials, the name of the Kicktipp group, the Zapier hook link in a `login_data.json` file. You can find an example in the `example_data.json` file.

Execute the commands below in the `Terminal`-Program:

```bash
python main.py
```

This lets the script run in the background without GUI and Zapier integration.

## Zapier Integration

If you want to receive a notification when the script tips for a match, you can use the Zapier integration. Please create a Zapier Account and set up the following Trigger: Custom Webhook. Please also make sure you set the ENV Variable `ZAPIER_URL` to the URL of your custom webhook. Then you can set up actions like sending an email or a push notification.

## xG Data & Result Prediction

The xG data is taken from the website [xGScore](https://xgscore.io/). The script uses the xG data to calculate the probability of a win, draw or loss for each team. Paired with the bookmakers' quotes, the script then determines a tip for the game, while also adding a random factor to the tip to not always tip the favorite.