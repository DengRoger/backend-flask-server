from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
import pydig
import time

from models import Domains, Records, Users, Glues, db, DDNS
from services import DNSService
import config


ddns = DDNS(logging, "/etc/ddnskey.conf", "172.21.21.3", "nycu-dev.me")

resolver = pydig.Resolver(
    executable='/usr/bin/dig',
    nameservers=[
        '172.21.21.3'
    ],
)

sql_engine = create_engine('sqlite:///:memory:')
db.Base.metadata.create_all(sql_engine)
Session = sessionmaker(bind=sql_engine)
session = Session()

users = Users(sql_engine)
domains = Domains(sql_engine)
records = Records(sql_engine)
glues = Glues(sql_engine)

dnsService = DNSService(logging, users, domains, records, glues, ddns, config.HOST_DOMAINS)

testdata = [("test-reg.nycu-dev.me", 'A', "140.113.89.64", 5),
            ("test-reg.nycu-dev.me", 'A', "140.113.64.89", 5)]
answer = {"140.113.89.64", "140.113.64.89"}

def test_domain_register():
    dnsService.register_domain("109550028", "test-reg.nycu-dev.me")
    for testcase in testdata:
        dnsService.add_record(*testcase)
    time.sleep(10)
    assert set(resolver.query("test-reg.nycu-dev.me", 'A')) == answer
    dnsService.release_domain("test-reg.nycu-dev.me")
    dnsService.register_domain("109550028", "test-reg.nycu-dev.me")
    time.sleep(10)
    assert set(resolver.query("test-reg.nycu-dev.me", 'A')) == set()

def test_duplicated_domain_register():
    dnsService.register_domain("109550028", "test-reg-dup.nycu-dev.me")
    try:
        dnsService.register_domain("109550028", "test-reg-dup.nycu-dev.me")
        assert 0
    except Exception:
        assert 1
    dnsService.release_domain("test-reg-dup.nycu-dev.me")

def test_nxdomain_operation():
    try:
        for testcase in testdata:
            dnsService.add_record(*testcase)
        assert 0
    except Exception:
        assert 1
    try:
        dnsService.release_domain("test-reg-nx.nycu-dev.me")
    except Exception:
        assert 1

def test_unhost_register():
    try:
        dnsService.register_domain("109550028", "www.google.com")
        assert 0
    except Exception:
        assert 1

def test_duplicated_record():
    dnsService.register_domain("109550028", "test-add-dup-rec.nycu-dev.me")
    dnsService.add_record("test-add-dup-rec.nycu-dev.me", 'A', "140.113.64.89", 5)
    try:
        dnsService.add_record("test-add-dup-rec.nycu-dev.me", 'A', "140.113.64.89", 5)
        assert 0
    except Exception:
        assert 1
    dnsService.release_domain("test-add-dup-rec.nycu-dev.me")

def test_glue_record():
    dnsService.register_domain("109550028", "test-glue.nycu-dev.me")

    dnsService.add_glue_record("test-glue.nycu-dev.me", "abc", "A", "1.1.1.1")
    time.sleep(5)
    assert set(resolver.query("abc.test-glue.nycu-dev.me", 'A')) == {"1.1.1.1"}
    
    dnsService.del_glue_record("test-glue.nycu-dev.me", "abc", "A", "1.1.1.1")
    time.sleep(5)
    assert set(resolver.query("abc.test-glue.nycu-dev.me", 'A')) == set()
    
    # check if glue record is be removed after domain released
    dnsService.add_glue_record("test-glue.nycu-dev.me", "abc", "A", "1.1.1.1")
    dnsService.release_domain("test-glue.nycu-dev.me")
    time.sleep(5)
    assert set(resolver.query("abc.test-glue.nycu-dev.me", 'A')) == set()
