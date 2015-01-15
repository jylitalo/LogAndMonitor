require_relative 'ylitalot_helper'

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
album_name = ARGV[1] if ARGV.length > 1

old_fname = find_post(post_name)
new_fname = old_fname + ".new"

album_name = find_album_name(old_fname) if not defined?(album_name)
if album_name.nil?
  puts "### G+ album name not defined as command line argument and missing from markdown file as well"
  exit 4
end # if

ifp = ImagesFromPicasa.new(nil)
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
