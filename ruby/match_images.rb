require_relative 'ylitalot_helper'

post_name = ARGV[0]
album_name = ARGV[1] if ARGV.length > 1

old_fname = find_post(post_name)
new_fname = old_fname + ".new"

album_name = find_album_name(old_fname) if not defined?(album_name)
if album_name.nil?
  puts "### G+ album name not defined as command line argument and missing from markdown file as well"
  exit 4
end # if

ifp = ImagesFromPicasa.new album_name
puts "### Found links for #{links.length} G+ images"

fin = File.open(old_fname)
fout = File.open(new_fname,"w")
fin.each_line do |line|
  if line.start_with?("{% slide /images")
    line = ifp.slide2gslide(line)
  elsif line.start_with?("{% gslide /images")
    ifp.slide2gslide(line)
  end # if
  fout.write(line)
end # fin.each_line
fout.write("\n<!-- G+: #{album_name} -->\n")
fout.close
fin.close

File.unlink(old_fname)
File.rename(new_fname,old_fname)
ifp.print_links
