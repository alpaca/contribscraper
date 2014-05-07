from bs4 import BeautifulSoup
import requests, urllib, sys
from models import Contributor, Committee
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

class BOEScraper(object):
	def __init__(self, db_url, base_url = "http://www.elections.il.gov/CampaignDisclosure/", debug=True):
		self.base_url = base_url
		self.debug = debug

		our_engine = create_engine(db_url)
		Session = sessionmaker(bind=our_engine)
		self.session = Session()
		return

	def scrape_candidate_links(self,party):
		url = self.base_url + "CandidateListPrint.aspx?LastNameSearchType=Starts%20with&LastName=&FirstNameSearchType=Starts%20with&FirstName=&AddressSearchType=Starts%20with&Address=&CitySearchType=Starts%20with&City=&State=&Zip=&ZipThru=&CanElectYear=&CanElectType=&CanOffice=&CanDistrictType=&CanDistrict=&CanParty=" + party + "&FairCampYes=&FairCampNo=&OrderBy=Last%20Name%20-%20A%20to%20Z"
		resp = requests.get(url)

		#<td headers="thCandidateName"><a href="CandidateDetail.aspx?ID=3946">
		soup = BeautifulSoup(resp.text)
		td_list = soup.findAll('td',{'headers':'thCandidateName'})
		committee_links = []
		for td in td_list:
			link = td.find('a')
			committee_links.append({'name': link.text, 'href': link['href']})
		return committee_links

	def scrape_candidate_committees(self,links):
		for link in links:
			if self.debug:
				print "Current link: %s" % link['href']
			url = self.base_url + link['href']
			resp = requests.get(url)
			soup = BeautifulSoup(resp.text)
			td_list = soup.findAll('td',{'class':'tdCandDetailCommitteeName'})
			for td in td_list:
				yield td.find('a').text, int(td.find('a')['href'].lower().split('?id=')[-1])
		return

	def parse_contrib_page(self,from_yr,to_yr,_from_month,_from_day):
		day = _from_day
		month = _from_month
		year = to_yr

		contrib_names_and_links = []

		while year > from_yr:
			from_day = day - 2
			if from_day < 1: from_day = 1
			url = self.base_url + "ContribListPrint.aspx?LastOnlyNameSearchType=Starts+with&LastOnlyName=&FirstNameSearchType=Starts+with&FirstName=&AddressSearchType=Starts+with&Address=&CitySearchType=Starts+with&City=&State=&Zip=&ZipThru=&ContributionType=All+Types&OccupationSearchType=Starts+with&Occupation=&EmployerSearchType=Starts+with&Employer=&VendorLastOnlyNameSearchType=Starts+with&VendorLastOnlyName=&VendorFirstNameSearchType=Starts+with&VendorFirstName=&VendorAddressSearchType=Starts+with&VendorAddress=&VendorCitySearchType=Starts+with&VendorCity=&VendorState=&VendorZip=&VendorZipThru=&OtherReceiptsDescriptionSearchType=&OtherReceiptsDescription=&PurposeState=Starts+with&Purpose=&Amount=100&AmountThru=" + str(499) + "&RcvDate=" + \
			urllib.quote('%i/%i/%i' % (month,from_day,year),safe='') + "&RcvDateThru=" + urllib.quote('%i/%i/%i' % (month,day,year),safe='') + "&Archived=false&QueryType=Contrib&LinkedQuery=false&OrderBy=Last+or+Only+Name+-+A+to+Z"
			if self.debug: print url
			resp = requests.get(url)
			soup = BeautifulSoup(resp.text)
			row_list = soup.findAll('tr')
			
			for idx,row in enumerate(row_list):
				if self.debug: print idx
				contrib_obj = {}
				for td in row.findAll('td'):
					try:
						print td['class']
						#This comparison is not working
						if td['class'] == "tdReceivedBy":
							print int(td.find('a')['href'].split('?ID=')[-1])
							contrib_obj[' '.join(td['class'])] = int(td.find('a')['href'].lower().split('?id=')[-1])
						else:
							contrib_obj[' '.join(td['class'])] = td.text.rstrip('\n "\t').lstrip('\n "\t')
					except Exception:
						pass
				if self.debug: 
					if contrib_obj != {}: print contrib_obj

				contrib_names_and_links.append(contrib_obj)
			day = from_day - 1
			if from_day <= 1:
				day = 30
				month = month - 1
				if month == 2:
					day = 28
				elif month < 1:
					month = 12
					year = year - 1

		return contrib_names_and_links

	def scrape_contributors(self):
		cur_yr = 2014
		while cur_yr > 2007:
			from_month = 5 if cur_yr == 2014 else 12
			from_day = 6 if cur_yr == 2014 else 30
			contrib_names_and_links = self.parse_contrib_page(from_yr=cur_yr-1, to_yr=cur_yr, _from_month=from_month, _from_day=from_day)
			for obj in contrib_names_and_links:
				if obj:
					try:
						c = Contributor(contributed_by = obj['tdContributedBy'],
									amount = obj['tdAmount'],
									received_by = obj['tdReceivedBy'],
									description = obj['tdDescription'],
									vendor_name = obj['tdVendorName'],
									vendor_address = obj['tdVendorAddress'],
									contrib_date=None,
									party=None)
					except KeyError:
						if 'tdContributedBy' in obj and 'tdAmount' in obj and 'tdReceivedBy' in obj:
							c = Contributor(contributed_by=obj['tdContributedBy'],
											received_by=obj['tdReceivedBy'],
											amount=obj['tdAmount'],
											party=None)
						else:
							c = None
					if c:
						self._fix_contributor(c)
						self.session.merge(c)
			cur_yr -= 1
			self.session.commit()
		return

	def scrape_contributor_party_aff(self,party):
		# def _is_in(comm_name,_contribs):
		# 	for contributor in _contribs:
		# 		if contributor and contributor.received_by:
		# 			if comm_name in contributor.received_by:
		# 				return contributor
		# 	return None

		links = self.scrape_candidate_links(party)

		# contributors = self.session.query(Contributor).all()
		# print contrib_by_committee_names.keys()

		for comm_name, comm_ID in self.scrape_candidate_committees(links):
			comm = Committee(committee_name = comm_name,
							committee_ID = comm_ID)

			self.session.merge(comm)
			# with open('committees.txt','a') as f:
			# 	f.write(comm_name + '\t\t' + str(href_list) + '\n')
			# if self.debug: print comm_name
			# # obj = _is_in(comm_name, contributors)
			# for idx,contrib in enumerate(contributors):
			# 	if self.debug and idx % 10000 == 0: print idx
			# 	rec_by = contrib.received_by
			# 	if contrib and rec_by:
			# 		if comm_name in contrib.received_by:
			# 			contrib.party = party
			# 			print contrib.party
			# 			print "ADDED PARTY YAY: %s" % party
			# 	# import pdb; pdb.set_trace()
			# 			self.session.merge(contrib)
			# 			print contrib
			# 			self.session.commit()
			# # print cand_name + ": " + str(href_list)

			self.session.commit()
		return

	def _fix_contributor(self,c):
			amnt_date = c.amount
			chunks = amnt_date.split('.')
			amnt = chunks[0]
			cents = chunks[1][:2]
			amnt = amnt + '.' + cents

			date = chunks[1][2:]
			c.amount = amnt
			c.contrib_date = datetime.strptime(date,'%m/%d/%Y')
			if self.debug: print "Parsed %s into:  %s  and  %s" % (amnt_date,amnt,str(c.contrib_date))
			return c

	def fix_amnt_and_date(self):
		contributors = self.session.query(Contributor).all()
		for c in contributors:
			c = self._fix_contributor(c)
			self.session.merge(c)
		self.session.commit()

####################

if __name__ == "__main__":
	scraper = BOEScraper(db_url='postgresql+psycopg2://postgres:postgres@localhost:5432/alpaca_api_development', debug=True)
	if len(sys.argv) != 3:
		print "usage: python boescraper.py scrape <contributors | party>"
	elif sys.argv[-1] == 'party':
		scraper.scrape_contributor_party_aff('Democratic')
	elif sys.argv[-1] == 'contributors':
		scraper.scrape_contributors()
	else:
		print "Unrecognized command."