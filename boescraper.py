from bs4 import BeautifulSoup
import requests, urllib
from models import Contributor

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
				yield td.find('a').text, td.find('a')['href']
		return

	def parse_contrib_page(self):
		day = 6
		month = 5
		year = 2014

		contrib_names_and_links = []

		while year >= 2014:
			from_day = day - 3
			if from_day < 1: from_day = 1
			url = self.base_url + "ContribListPrint.aspx?LastOnlyNameSearchType=Starts+with&LastOnlyName=&FirstNameSearchType=Starts+with&FirstName=&AddressSearchType=Starts+with&Address=&CitySearchType=Starts+with&City=&State=&Zip=&ZipThru=&ContributionType=All+Types&OccupationSearchType=Starts+with&Occupation=&EmployerSearchType=Starts+with&Employer=&VendorLastOnlyNameSearchType=Starts+with&VendorLastOnlyName=&VendorFirstNameSearchType=Starts+with&VendorFirstName=&VendorAddressSearchType=Starts+with&VendorAddress=&VendorCitySearchType=Starts+with&VendorCity=&VendorState=&VendorZip=&VendorZipThru=&OtherReceiptsDescriptionSearchType=&OtherReceiptsDescription=&PurposeState=Starts+with&Purpose=&Amount=100&AmountThru=499&RcvDate=" + \
			urllib.quote('%i/%i/%i' % (month,from_day,year),safe='') + "&RcvDateThru=" + urllib.quote('%i/%i/%i' % (month,day,year),safe='') + "&Archived=false&QueryType=Contrib&LinkedQuery=false&OrderBy=Last+or+Only+Name+-+A+to+Z"
			if self.debug: print url
			resp = requests.get(url)
			soup = BeautifulSoup(resp.text)
			row_list = soup.findAll('tr')
			
			for idx,row in enumerate(row_list):
				if self.debug: print idx
				contrib_obj = {}
				for td in row.findAll('td'):
					if td.get('class'):
						print td['class']
						contrib_obj[' '.join(td['class'])] = td.text.rstrip('\n "\t').lstrip('\n "\t')
				if self.debug: 
					if contrib_obj != {}: print contrib_obj

				contrib_names_and_links.append(contrib_obj)
			day = from_day
			if from_day == 1:
				day = 30
				month = month - 1
				if month < 1:
					month = 12
					year = year - 1

		return contrib_names_and_links

	def scrape_contributors(self):
		contrib_names_and_links = self.parse_contrib_page()
		for obj in contrib_names_and_links:
			if obj:
				if self.debug: print "got obj."
				c = Contributor(contributed_by = obj['tdContributedBy'],
								amount = obj['tdAmount'],
								received_by = obj['tdReceivedBy'],
								description = obj['tdDescription'],
								vendor_name = obj['tdVendorName'],
								vendor_address = obj['tdVendorAddress'],
								party=None)
				self.session.merge(c)
				self.session.commit()
		return

	def scrape_contributor_party_aff(self,party):
		def _is_in(comm_name,_contribs):
			for contributor in _contribs:
				if contributor and contributor.received_by:
					if comm_name in contributor.received_by:
						return contributor
			return None

		links = self.scrape_candidate_links(party)

		contributors = self.session.query(Contributor).all()
		# print contrib_by_committee_names.keys()

		for comm_name, href_list in self.scrape_candidate_committees(links):
			if self.debug: print comm_name
			obj = _is_in(comm_name, contributors)
			if obj:
				obj.party = party
				print obj.party
				print "ADDED PARTY YAY: %s" % party
				import pdb; pdb.set_trace()
				self.session.merge(obj)
				print obj
				self.session.commit()
			# print cand_name + ": " + str(href_list)
		return

####################

scraper = BOEScraper(db_url='postgresql+psycopg2://postgres:postgres@localhost:5432/alpaca_api_development', debug=True)
scraper.scrape_contributors()
scraper.scrape_contributor_party_aff('Democratic')