require_relative 'ylitalot_helper'

def extract_slides(fname)
  slides = []
  f = File.open(fname)
  f.each_line do |line|
    if line.start_with?("{% slide /images")
      slides += [extract_jpg(line)]
    end # if
  end # f.each_line
  f.close
  return slides
end # extract_slides

def establish_target_dir(post_name)
  home = Dir.home()
  dir = "#{home}/kuvat/net2google/#{post_name}"
  unless Dir.exists?(dir)
    puts "### #{dir} created."
    Dir.mkdir(dir)
  else
    puts "### #{dir} found."
  end # unless
  return dir
end # establish_target_dir

def find_image(jpg)
  home = Dir.home()
  jpeg_home = "#{home}/kuvat/jpg"
  image = Dir.glob("#{jpeg_home}/#{jpg}.*")[0]
  if image.nil?
    jpg.sub!("/IMG_", "/img_")
    image = Dir.glob("#{jpeg_home}/#{jpg}.*")[0]
  end
  if image.nil?
    puts "### Unable to find original image for #{jpg}"
    puts "### jpeg_home = #{jpeg_home}"
  end # if
  return image
end # find_image

post_name = ARGV[0]
album_name = ARGV[1]
password = ARGV[2]

post_fname = find_post(post_name)

### 
# Create album into G+
###
ifp = ImagesFromPicasa.new(password)
album_id = ifp.create_album(album_name)

###
# Find slides in a post, create images and upload them.
###
slides = extract_slides(post_fname)
target_dir = establish_target_dir(post_name)

slides.each do |jpg|
  fname = jpg.split("/").last
  original = find_image(jpg)
  img = "#{target_dir}/#{fname}.jpg"
  unless File.exists?(img)
    cmd = "convert -resize 2000x2000 #{original} #{img}"
    puts "### #{cmd}"
    system cmd
  end # unless File.exists?(img)
  ifp.send_photo(img)
  File.unlink(img)
end # slides.each

###
# Fix links in post
###
new_fname = post_fname + ".new"

fin = File.open(post_fname)
fout = File.open(new_fname,"w")
fin.each_line do |line|
  if line.start_with?("{% slide /images")
    line = ifp.slide2gslide(line)
  elsif line.start_with?("{% gslide /images")
    ifp.slide2gslide(line)
  end # if
  fout.write(line) unless line.start_with?("<!-- G+: ")
end # fin.each_line
fout.write("\n<!-- G+: #{album_name} -->\n")
fout.close
fin.close

File.unlink(post_fname)
File.rename(new_fname,post_fname)

#unless ifp.links.empty?
#  puts "Following images were found from G+, but no matching images in markdown"
#  puts links
#end # if
Dir.rmdir(target_dir)
