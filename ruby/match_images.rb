require_relative 'ylitalot_helper'

post_name = ARGV[0]
gp_links = ARGV[1]
old_fname = find_post(post_name)
new_fname = old_fname + ".new"

fgp = File.open(gp_links)
gp_links = {}
resolution="w1280-h850"
fgp.each_line do |line|
  line = line.strip
  line.sub!(/\/w[0-9]+-h[0-9]+-no\//,"/#{resolution}-no/")
  line.sub!(/\/s[0-9]+-no\//,"/#{resolution}-no/")
  jpg = line.split("/").last
  gp_links[jpg] = line
end
fgp.close
puts "### found links for #{gp_links.length} G+ images"

fin = File.open(old_fname)
fout = File.open(new_fname,"w")
fin.each_line do |line|
  if line.start_with?("{% slide /images")
    jpg = extract_jpg(line).split("/").last
    if gp_links.has_key?(jpg + ".jpg")
      line.sub! "{% slide ", "{% gslide "
      line.sub! " %}", " #{gp_links[jpg + ".jpg"]} %}"
    elsif gp_links.has_key?(jpg + ".JPG")
      line.sub! "{% slide ", "{% gslide "
      line.sub! " %}", " #{gp_links[jpg + ".JPG"]} %}"
    else
      puts "Unable to find G+ image for #{jpg}"
    end # if gp_links.has_key?
  end # if line.starts_with?
  fout.write(line)
end # fin.each_line
fout.close
fin.close
