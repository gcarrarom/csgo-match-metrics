#%%
from cloudscraper import CloudScraper
from bs4 import BeautifulSoup
import re
from copy import deepcopy
from collections import defaultdict
from sys import argv

match_id = argv[1]
cs = CloudScraper()

headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

body = {
    "sharecode": match_id
}

test = cs.post(f"https://csgostats.gg/match/upload/ajax", data=body, headers=headers)

# %%
match_upload_data = test.json()

csdata_request = cs.get(match_upload_data['data']['url'])

# %%

data = []
soup = BeautifulSoup(csdata_request.text, features="html.parser")

#%%
table = soup.find('table', attrs={'class': 'scoreboard'})
table_body = table.find_all('tbody')
data.append(["MatchID", "Date", "Map"] + [col.text.strip() for col in table.find('thead').find('tr', attrs={'class': 'absolute-spans'}).find_all('th')] + ["Teammate" + str(i+1) for i in range(5)])

team_1_table = table_body[0]
team_2_table = table_body[2]

date_to_convert = soup.find('div', attrs={'class', 'match-date-text'}).text
date_found = re.findall(r'([0-9]{1,2})[thstrd]{1,2} ([a-zA-Z]{3}) ([0-9]{4})', date_to_convert)

today = f"{date_found[0][0]}-{date_found[0][1]}-{date_found[0][2]}"


map_name = soup.find('div', attrs={'class', 'map-text'}).text


team_1_teammates = []
for row in team_1_table.find_all('tr')[1:]:
    team_1_teammates.append(row.find_all('td')[0].text.strip())
for row in team_1_table.find_all('tr')[1:]:
    data.append([match_id, today, map_name] + [col.text.strip() for col in row.find_all('td')] + team_1_teammates)
team_2_teammates = []
for row in team_2_table.find_all('tr')[1:]:
    team_2_teammates.append(row.find_all('td')[0].text.strip())
for row in team_2_table.find_all('tr')[1:]:
    data.append([match_id, today, map_name] + [col.text.strip() for col in row.find_all('td')] + team_2_teammates)

with open('total.csv', 'w', encoding="utf-8") as file_writer:
    file_writer.write("\n".join([",".join([col for col in row]) for row in data]))
# %%

csdata_request = cs.get(match_upload_data['data']['url'] + '#/rounds')
# %%
clutches = {player: defaultdict(int) for player in team_1_teammates + team_2_teammates}
data = []
soup = BeautifulSoup(csdata_request.text, features="html.parser")
data.append(['round', 'tick', 'killer', 'assist', 'weapon', 'headshot', 'killed'])
for i, round_info_div in enumerate(soup.find_all('div', attrs={'class': 'round-info'})):
    team_1_alive = deepcopy(team_1_teammates)
    team_2_alive = deepcopy(team_2_teammates)
    clutch_1 = False
    clutch_2 = False
    for inner in round_info_div.find_all('div', attrs={'class': 'round-info-side'})[1].find_all('div', attrs={'class': 'tl-inner'}):
        row = []
        # Round number
        row.append(i+1)

        # Appending tick
        spans = inner.find_all('span')
        row.append(spans[0].text.strip())
        
        # Appending killer
        ct_spans = inner.find_all('span', attrs={'class': 'team-ct'})
        t_spans = inner.find_all('span', attrs={'class': 'team-t'})

        row.append(spans[1].text.strip())
        if (len(ct_spans) + len(t_spans)) > 2:
            row.append(spans[2].text.strip())
            killed = spans[3].text.strip()
        else:
            row.append('')
            killed = spans[2].text.strip()

        # Appending weapon
        weapon_imgs = inner.find_all('img')
        if len(weapon_imgs) == 0:
            weapon = inner.text.split()
        else:
            weapon = weapon_imgs[0].attrs['alt']
        row.append(weapon)

        # Appending headshot
        test = True if type(inner.find_all('img', attrs={'alt':'Headshot'})) is not None else False
        row.append(test)

        # Appending killed
        row.append(killed)
        
        if not clutch_1 or not clutch_2:
            if killed in team_2_alive:
                team_2_alive.remove(killed)
            elif killed in team_1_alive:
                team_1_alive.remove(killed)
            
            if not clutch_1:
                if len(team_1_alive) == 1:
                    clutch_1 = True
                    clutches[team_1_alive[0]][len(team_2_alive)] += 1
                    print(f"{team_1_alive[0]} did a 1v{len(team_2_alive)} clutch on the round {i+1}")
            if not clutch_2:
                if len(team_2_alive) == 1:
                    clutch_2 = True
                    clutches[team_2_alive[0]][len(team_1_alive)] += 1
                    print(f"{team_2_alive[0]} did a 1v{len(team_1_alive)} clutch on the round {i+1}")
        # Appending row
        data.append(row)


clutch_table = []
clutch_table.append(["MapID", "Date", "Map", "Player", "1v1", "1v2", "1v3", "1v4", "1v5"])
for player in clutches:
    clutch_table.append([match_id, today, map_name, player, clutches[player][1], clutches[player][2], clutches[player][3], clutches[player][4], clutches[player][5]])

with open('clutches.csv', 'w', encoding="utf-8") as fw:
    fw.write("\n".join([",".join([str(col) for col in row]) for row in clutch_table]))


with open('rounds.csv', 'w', encoding="utf-8") as file_writer:
    file_writer.write("\n".join([",".join([str(col) for col in row]) for row in data]))
# %%
#roud_info_divs[1].find_all('div', attrs={'class': 'tl-inner'})[0].find_all('span')

# %%
