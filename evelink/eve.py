from evelink import api

class EVE(object):
    """Wrapper around /eve/ of the EVE API."""

    @api.auto_api
    def __init__(self, api=None):
        self.api = api

    def character_ids_from_names(self, name_list):
        """Retrieve a dict mapping character names to IDs.

        name_list:
            A list of names to retrieve character IDs.

        Names of unknown characters will map to None.
        """

        api_result = self.api.get('eve/CharacterID', {
                'names': set(name_list),
            })

        rowset = api_result.find('rowset')
        rows = rowset.findall('row')

        results = {}
        for row in rows:
            name = row.attrib['name']
            char_id = int(row.attrib['characterID']) or None
            results[name] = char_id

        return results

    def character_id_from_name(self, name):
        """Retrieve the named character's ID.

        Convenience wrapper around character_ids().
        """
        return self.character_ids_from_names([name]).get(name)

    def character_info_from_id(self, char_id):
        """Retrieve a dict of info about the designated character."""

        api_result = self.api.get('eve/CharacterInfo', {
                'characterID': char_id,
            })

        def _str(key): return api.get_named_value(api_result, key)
        def _int(key): return api.get_int_value(api_result, key)
        def _ts(key): return api.get_ts_value(api_result, key)
        def _float(key):
            val = _str(key)
            return float(val) if val is not None else None

        results = {
            'id': _int('characterID'),
            'name': _str('characterName'),
            'race': _str('race'),
            'bloodline': _str('bloodline'),
            'sec_status': _float('securityStatus'),
            'skillpoints': _int('skillPoints'),
            'location': _str('lastKnownLocation'),
            'isk': _float('accountBalance'),

            'corp': {
                'id': _int('corporationID'),
                'name': _str('corporation'),
                'timestamp': _ts('corporationDate'),
            },

            'alliance': {
                'id': _int('allianceID'),
                'name': _str('alliance'),
                'timestamp': _ts('allianceDate'),
            },

            'ship': {
                'name': _str('shipName'),
                'type_id': _int('shipTypeID'),
                'type_name': _str('shipTypeName'),
            },
            
            'history': [],
        }

        # Add in corp history
        history = api_result.find('rowset')
        for row in history.findall('row'):
            corp_id = row.attrib['corporationID']
            start_date = api.parse_ts(row.attrib['startDate'])
            results['history'].append({
                    'corp_id': corp_id,
                    'start_ts': start_date,
                })

        return results

    def alliances(self):
        """Return a dict of all alliances in EVE."""

        api_result = self.api.get('eve/AllianceList')

        results = {}
        rowset = api_result.find('rowset')
        for row in rowset.findall('row'):
            alliance = {
                'name': row.attrib['name'],
                'ticker': row.attrib['shortName'],
                'id': int(row.attrib['allianceID']),
                'executor_id': int(row.attrib['executorCorpID']),
                'member_count': int(row.attrib['memberCount']),
                'timestamp': api.parse_ts(row.attrib['startDate']),
                'member_corps': {},
            }

            corp_rowset = row.find('rowset')
            for corp_row in corp_rowset.findall('row'):
                corp_id = int(corp_row.attrib['corporationID'])
                corp_ts = api.parse_ts(corp_row.attrib['startDate'])
                alliance['member_corps'][corp_id] = {
                    'id': corp_id,
                    'timestamp': corp_ts,
                }

            results[alliance['id']] = alliance

        return results
