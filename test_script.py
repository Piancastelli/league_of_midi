from pprint import pprint, pformat
from random import choice
import datetime

import requests
import midiutil as mu


def midi_test():
    test_midi = mu.MIDIFile()
    test_midi.addTempo(0, 0, 182)

    major_offset = [0, 2, 4, 5, 7, 9, 11]
    minor_offset = [0, 2, 3, 5, 7, 8, 10]

    notes = []
    for i, note in enumerate(range(8)):
        noteval = 60 + choice(minor_offset)
        test_midi.addNote(0, 0, noteval, i, 0.85, 96)
        notes.append(noteval)

    print(notes)

    with open("test_midi.mid", "wb") as file:
        test_midi.writeFile(file)


class GameData(object):
    def __init__(self, summoner_name="bloodyak", match_number=1, server="euw1"):
        self.summoner = summoner_name
        self.match = match_number
        self.server = server

        # Set up DataDragon parameters
        self.dd_base = "https://ddragon.leagueoflegends.com"
        self.dd_version = requests.get("{}/api/versions.json".format(self.dd_base)).json()[0]
        self.dd_champ_keys = requests.get("{}/cdn/{}/data/en_US/championFull.json".format(self.dd_base, self.dd_version)).json()["keys"] # NOQA: E501
        self.dd_items = requests.get("{}/cdn/{}/data/en_US/item.json".format(self.dd_base, self.dd_version)).json()

        # Riot API stuff
        self.base = "https://{}.api.riotgames.com".format(self.server)
        self.headers = {"X-Riot-Token": API_KEY, "Origin": "https://developer.riotgames.com"}
        self.acc_id = self._get_account_id()

    def generate_address(self, route):
        """Prepend the Riot base address to the route that gets passed in.
        The route requires the '/' at the start"""
        url = "{}{}".format(self.base, route)
        return url

    def parse_json(self, req):
        """Catch errors in the event the response content isn't valid JSON"""
        try:
            retval = req.json()
        except ValueError:
            assert "Response not JSON format: {}".format(req.content)

        return retval

    def _get_account_id(self):
        """Return the account ID of the summoner name"""
        url = self.generate_address("/lol/summoner/v3/summoners/by-name/{}".format(self.summoner))
        resp = requests.get(url, headers=self.headers)

        return self.parse_json(resp)["accountId"]

    def get_dd_single_champ_json(self):
        """Returns the JSON data for the champ that the summoner played in their given match"""
        champ_key = str(self.get_single_match_by_account()["matches"][0]["champion"])

        for champid, champ in self.dd_champ_keys.items():
            if champid == champ_key:
                champ_name = champ
                break

        champ_url = "{}/cdn/{}/data/en_US/champion/{}.json".format(self.dd_base, self.dd_version, champ_name)
        champ_json = self.parse_json(requests.get(champ_url))

        return champ_json

    def get_single_match_by_account(self):
        """Returns the response JSON for the match when searched by-account"""
        summoner_url = self.generate_address("/lol/match/v3/matchlists/by-account/{}".format(self.acc_id))

        # Passing match_number as the endIndex means the last item in the 'matches' list will always be the game we want
        summoner_resp = requests.get(summoner_url, headers=self.headers, params={"endIndex": self.match})

        return self.parse_json(summoner_resp)

    def get_single_match_by_match_id(self):
        """Returns the response JSON for the match ID of the given game"""
        summoner_url = self.generate_address("/lol/match/v3/matchlists/by-account/{}".format(self.acc_id))

        # Passing match_number as the endIndex means the last item in the 'matches' list is the game we want
        summoner_resp = requests.get(summoner_url, headers=self.headers, params={"endIndex": self.match})

        match_id = self.parse_json(summoner_resp).get("matches")[-1].get("gameId")

        if match_id:
            match_url = self.generate_address("/lol/match/v3/matches/{}".format(self.match_id))
        else:
            assert "Invalid formatting in response: {}".format(summoner_resp)

        match_resp = requests.get(match_url, headers=self.headers)

        return self.parse_json(match_resp)


if __name__ == '__main__':
    # resp = get_single_match_by_match_id("bloodyak")
    # create_time = datetime.datetime.fromtimestamp(resp.get("gameCreation")/1000)
    # print(create_time.strftime("%H:%M:%S  %B %d"))
    game = GameData()
    # pprint(game.dd_champ_keys)

    # for champ in game.dd_champ_keys.values():
    #     req = requests.get("{}/cdn/{}/data/en_US/champion/{}.json".format(game.dd_base, game.dd_version, champ))   
    #     print(champ, req.status_code)
    #     assert req.status_code == 200
