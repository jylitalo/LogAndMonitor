#!/usr/bin/ruby
require "rubygems"
require "optparse"
require "watir-webdriver"

class KuvatFi
  attr_accessor :browser, :debug

  def initialize()
    @debug = false
    @browser = Watir::Browser.new :ff
  end

  def rip(url)
    @browser.goto(url)
    sleep 30
    visited = 0
    newurls = []

    imgs = @browser.divs.find_all { |i| i.class_name =~ /imageobject/ }
    imgs.each do |img|
      visited += 1
      fname = img.attribute_value("data-filename")
      d = img.span(:class,'date').text
      print("\n\n[[" + url + "][" + fname + "][" + d + "][#" + visited.to_s + "]]\n")
      print "" + img.title
    end
    albums = @browser.divs.find_all { |a| a.class_name =~ /album/ }
    albums.each do |album|
      album = album.a(:class,"name")
      if album.exists?
        newurls.push(album.href)
      end
    end
    return newurls.uniq
  end

  def close()
    browser.close
  end
end

debug = false
if __FILE__ == $0
  # parse command line arguments
  options = {}
  options[:url] = []
  OptionParser.new do |opts|
    opts.banner = "Usage: edit_selected.rb [options] host dir"
    opts.on('-u','--url url','URL for root album') do |u|
      options[:url].push(u)
    end
    options[:debug] = false
    opts.on('-d','--debug','Enable debug information') do |d|
      options[:debug] = true
    end
  end.parse!
  # print "URL :: >#{options[:url]}<\n" if debug
  raise "URL is missing" if options[:url].length == 0

  kuvat = KuvatFi.new
  kuvat.debug = options[:debug]
  round = 0
  while options[:url].length > 0
    round += 1
    newurls = []
    options[:url].each { |url|
      newurls += kuvat.rip(url)
    }
    options[:url] = newurls
    # print "### round " + round.to_s + " completed"
    # print "### options is " + options[:url].length.to_s + " long"
  end
  kuvat.close
  # print "Script completed\n" 
end
