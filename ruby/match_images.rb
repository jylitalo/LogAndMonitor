require_relative 'ylitalot_helper'
require 'Picasa' 

class ImagesFromPicasa
  def initialize
    @client = Picasa::Client.new(user_id: "juha.ylitalo@gmail.com")
  end # initialize

  def find_album_id(name)
    albums = []
    @client.album.list.entries.each do |album|
      if album.title == name
        puts "### Found album id ##{album.id} for #{name}"
        return album.id
      else
        albums += [album.title]
      end # if album.title ...
    end # client.album.list.entries.each
      
    albums.sort!
    puts "### No album id found for #{name}"
    puts "### Found following albums: #{albums.to_s}"
    exit 3
  end # find_album_id

  def fetch_links(album)
    resolution="w1280-h800"
    links = {}
    album_id = self.find_album_id(album)
    @client.album.show(album_id).entries.each do |photo|
      url = photo.media.thumbnails[0].url
      url.sub!(/\/s[0-9]+\//,"/#{resolution}-no/")
      jpg = url.split("/").last
      puts "### JPG = >#{jpg}< >#{url}<"
      links[jpg] = url
    end # client.album.show().entries
    return links
  end # fetch_links
end # class ImagesFromPicasa

def slide2gslide(line,links)
  jpg = extract_jpg(line).split("/").last
  suffix = nil
  if links.has_key?(jpg + ".jpg")
    suffix = ".jpg"
  elsif links.has_key?(jpg + ".JPG")
    suffix = ".JPG"
  else
    puts "Unable to find G+ image for #{jpg}"
    return line
  end # if

  if line.start_with?("{% slide /images")
    line.sub! "{% slide ", "{% gslide "
    line.sub! " %}", " #{links[jpg + suffix]} %}"
  end # if
  links.delete(jpg + suffix)
  return line
end # slide2gslide

post_name = ARGV[0]
album_name = ARGV[1]

old_fname = find_post(post_name)
new_fname = old_fname + ".new"

ifp = ImagesFromPicasa.new
links = ifp.fetch_links(album_name)
puts "### Found links for #{links.length} G+ images"

fin = File.open(old_fname)
fout = File.open(new_fname,"w")
fin.each_line do |line|
  if line.start_with?("{% slide /images")
    line = slide2gslide(line,links)
  elsif line.start_with?("{% gslide /images")
    slide2gslide(line,links)
  end # if
  fout.write(line)
end # fin.each_line
fout.write("\n<!-- G+: #{album_name} -->\n")
fout.close
fin.close

if not links.empty?
  puts "Following images were found from G+, but no matching images in markdown"
  puts links
end # if

File.unlink(old_fname)
File.rename(new_fname,old_fname)
