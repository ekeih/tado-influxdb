#! /usr/bin/env python3

import fake_useragent
import influxdb
import json
import requests
import time

import config

class Tado:
  username       = ''
  password       = ''
  useragent      = fake_useragent.UserAgent(fallback='Mozilla/5.0 (X11; OpenBSD amd64; rv:28.0) Gecko/20100101 Firefox/28.0')
  headers        = {
    'Referer'    : 'https://my.tado.com',
    'Origin'     : 'https://my.tado.com',
    'User-Agent' : useragent.random
  }
  api            = 'https://my.tado.com/api/v2/homes'
  access_token   = ''
  access_headers = headers
  refresh_token  = ''
  modes          = {
    'HOME'  : 0,
    'AWAY'  : 1,
    'SLEEP' : 2
  }


  def __init__(self, username, password):
    self.username = username
    self.password = password
    self._login()
    self.id = self._getMe()['homes'][0]['id']

  def _login(self):
    url='https://auth.tado.com/oauth/token'
    data = {
      'client_id'     : 'tado-web-app',
      'client_secret' : 'wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc',
      'grant_type'    : 'password',
      'password'      : self.password,
      'scope'         : 'home.user',
      'username'      : self.username
    }
    request = requests.post(url, data=data, headers=self.access_headers)
    response = request.json()
    self.access_token = response['access_token']
    self.refresh_token = response['refresh_token']
    self.access_headers['Authorization'] = 'Bearer ' + response['access_token']

  def _apiCall(self, cmd):
    url = '%s/%i/%s' % (self.api, self.id, cmd)
    request = requests.get(url, headers=self.access_headers)
    response = request.json()
    return response

  def _getMe(self):
    url = 'https://my.tado.com/api/v2/me'
    request = requests.get(url, headers=self.access_headers)
    response = request.json()
    return response

  def _getState(self, zone):
    cmd = 'zones/%i/state' % zone
    data = self._apiCall(cmd)
    return data

  def _getWeather(self):
    cmd = 'weather'
    data = self._apiCall(cmd)
    return { 'outside_temperature' : data['outsideTemperature']['celsius'],
             'solar_intensity'     : data['solarIntensity']['percentage']
           }

  def refreshAuth(self):
    url='https://auth.tado.com/oauth/token'
    data = {
      'client_id'     : 'tado-web-app',
      'client_secret' : 'wZaRN7rpjn3FoNyF5IFuxg9uMzYJcvOoQ8QWiIqS3hfk6gLhVlG57j5YNoZL2Rtc',
      'grant_type'    : 'refresh_token',
      'refresh_token' : self.refresh_token,
      'scope'         : 'home.user'
    }
    request = requests.post(url, data=data, headers=self.headers)
    response = request.json()
    self.access_token = response['access_token']
    self.refresh_token = response['refresh_token']
    self.access_headers['Authorization'] = 'Bearer ' + self.access_token

  def getZone(self, zone):
    state = self._getState(zone)
    current_temperature = float(state['sensorDataPoints']['insideTemperature']['celsius'])
    humidity            = float(state['sensorDataPoints']['humidity']['percentage'])
    heating_power       = float(state['activityDataPoints']['heatingPower']['percentage'])
    tado_mode           = state['tadoMode']
    if state['setting']['power'] == 'ON':
      wanted_temperature = float(state['setting']['temperature']['celsius'])
    else:
      wanted_temperature = current_temperature
    weather = self._getWeather()
    outside_temperature = float(weather['outside_temperature'])
    solar_intensity = float(weather['solar_intensity'])
    return {
      'outside_temperature' : outside_temperature,
      'solar_intensity'     : solar_intensity,
      'current_temperature' : current_temperature,
      'wanted_temperature'  : wanted_temperature,
      'humidity'            : humidity,
      'heating_power'       : heating_power,
      'tado_mode'           : self.modes[tado_mode]
    }

if __name__ == '__main__':

  influxdb_client = influxdb.InfluxDBClient(host=config.influxdb_host, port=config.influxdb_port, database=config.influxdb_database)
  tado = Tado(config.tado_user, config.tado_pass)

  while True:
    tado.refreshAuth()
    measurements = []
    for id, name in config.tado_zones.items():
      result           = { "measurement": config.influxdb_measurement }
      result["tags"]   = { "room": name }
      result["fields"] = tado.getZone(id)
      print('[%s] %s' % (datetime.datetime.now().isoformat(), result))
      measurements.append(result)
    influxdb_client.write_points(measurements)
    time.sleep(15)
