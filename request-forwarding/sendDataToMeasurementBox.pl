#!/usr/bin/env perl
use MIME::Base64;
use HTTP::Request;
use LWP::UserAgent;
use lib "/Library/Perl/5.18";
use JSON::Parse "parse_json";
use JSON;
use Data::Dumper;

$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME} = 0;

my $username = <STDIN>;
my $password = <STDIN>;
my $remote_addr = <STDIN>;
my $result = <STDIN>;
my $timestamp = <STDIN>;
my $json_str = <STDIN>;
my $request_headers = parse_json($json_str);


print "DEBUG: $username >>  $password >>  $remote_addr >> $result $json_str";

# Construct the HTTP Request
my $url = "CHANGEME/login/";
my %content = (
    "username" => $username,
    "password" => $password,
    "remote_addr" => $remote_addr,
    "result" => $result,
    "timestamp" => $timestamp,
    "request_headers" => $request_headers
);

my $req = HTTP::Request->new("POST", $url);
$req->content_type("application/json");
$req->content(encode_json(\%content));

my $lwp = LWP::UserAgent->new;
my $result = $lwp->request($req);

if ($result->is_success) {
    print "Success\n";
} else {
    print "Error: ".$result->status_line."\n";
}
