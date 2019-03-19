import os
import time
import re
import datetime
import csv
import pandas as pd
from slackclient import SlackClient




slack_client = SlackClient('xoxb-4131852739-583201881750-O06yuloGunK4Y6GlNX5VqwTC')

USERNAME_REGEX = "^<@U$"


def send_response_to_channel(message, channel):
	slack_client.api_call("chat.postMessage", channel=channel, text=message)


def get_all_existing_users():
	all_slack_users = []

	api_call = slack_client.api_call("users.list")

	if api_call.get('ok'):
		users = api_call['members']
		for user in users:
			all_slack_users.append({"user_id": user['id'], "real_name": user['real_name']})

		return all_slack_users


def get_a_user_info(user_id):
	api_call = slack_client.api_call("users.info", user=user_id)

	if api_call.get('ok'):
		user_name = api_call['user']['name']

		return user_name


def write_to_csv():

	header = ['receiver_user_id', 'receiver_name', 'giver_user_id', 'date']

	with open("kudos.csv", "w", newline='') as f:
		writer = csv.writer(f, delimiter=',')
		writer.writerow(header)

	f.close()


def append_to_existing_csv(row):

	with open('kudos.csv', 'a') as f:
		writer = csv.writer(f, delimiter=',')
		writer.writerow(row)

	f.close()



def get_the_leaderboard():
	 
	data = pd.read_csv("kudos.csv") 
	lb = data['receiver_name'].value_counts()
	
	receiver = lb.keys().tolist()
	kudos_no = lb.tolist()

	results = [a for a in zip(receiver, kudos_no)]

	return results


def has_posted_today(giver_user_id):
	data = pd.read_csv("kudos.csv") 

	for key, row in data.iterrows():
		kudos_date_obj = datetime.datetime.strptime(row['date'], '%Y-%m-%d')

		# print(row['giver_user_id'], giver_user_id)
		# print("------------")
		# print(kudos_date_obj.date(), datetime.datetime.today().date())


		if row['giver_user_id'] == giver_user_id and kudos_date_obj.date() == datetime.datetime.today().date():

			return True

	return False
	





def parse_slack_events(slack_events):

	"""
	Get all slack events and check if it contains the word `Kudos` and a user
	"""

	for event in slack_events:

		if event["type"] == "message" and not "subtype" in event:

			words_in_text = event["text"].split(" ")

			first_word_in_text = words_in_text[0]

			if len(words_in_text) > 1:

				second_word_in_text = words_in_text[1]
			else:
				second_word_in_text = "nothing"

			regx = re.compile(USERNAME_REGEX)

			if first_word_in_text.lower() == "kudos":
				print("the slack text is ==== ", event["text"])

				for word in words_in_text:

					if regx.match(word[0:3]):

						giver = event["user"]
						receiver = word[2:-1]

						giver_name = get_a_user_info(giver)
						receiver_name = get_a_user_info(receiver)

						posted = has_posted_today(giver)

						print(posted)

						if posted != True:

							given_on = datetime.datetime.today().date()

							row_data = [receiver, receiver_name, giver, given_on]

							append_to_existing_csv(row_data)

							message = ':thumbsup: `{}` has just received a `Kudo` from `{}`. Keep the Kudos coming in.'.format(receiver_name, giver_name)

							send_response_to_channel(message, event["channel"])
						else:
							message = '@{} you have already given out a Kudos today. `Great job!`'.format(giver_name)

							send_response_to_channel(message, event["channel"])


			elif regx.match(first_word_in_text[0:3]) and second_word_in_text.lower() == "leaderboard":

				lb = get_the_leaderboard()

				send_response_to_channel(lb, event["channel"])

			elif regx.match(first_word_in_text[0:3]) and second_word_in_text.lower() == "help":

				message = """- Start your message with Kudos, mention the receiver and say why. For example: `Kudos to @naanamensa for helping me out with my issue today.` 
- Want help? Do `@kudobot help`
- Want the leaderboard? Do `@kudobot leaderboard`
					"""

				send_response_to_channel(message, event["channel"])
				




if __name__ == "__main__":

	if slack_client.rtm_connect():
		print("Kudobot connected and running!")

		while True:
			parse_slack_events(slack_client.rtm_read())

			time.sleep(1)
	else:
		print("Connection failed. Exception traceback printed above.")