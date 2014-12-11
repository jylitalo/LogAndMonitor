require_relative 'ylitalot_helper'

post_name = ARGV[0]
slides = []

f = File.open(find_post(post_name))
f.each_line do |line|
  if line.start_with?("{% slide /images")
    slides += [extract_jpg(line)]
  end # if
end # f.each_line
f.close

home = Dir.home()
jpeg_home = "#{home}/kuvat/jpg"
target_dir = "#{home}/kuvat/net2google/#{post_name}"
unless Dir.exists?(target_dir)
  puts "### #{target_dir} created."
  Dir.mkdir(target_dir)
else
  puts "### #{target_dir} found."
end # unless

slides.each do |jpg|
  fname = jpg.split("/").last
  original = Dir.glob("#{jpeg_home}/#{jpg}.*")[0]
  if not original
    jpg.sub!("/IMG_", "/img_")
    original = Dir.glob("#{jpeg_home}/#{jpg}.*")[0]
  end
  img = "#{target_dir}/#{fname}.jpg"
  unless File.exists?(img)
    cmd = "convert -resize 2000x2000 #{original} #{img}"
    puts "### #{cmd}"
    system cmd
  end # unless
end # slides.each
