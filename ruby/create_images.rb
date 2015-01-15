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
  if not image
    jpg.sub!("/IMG_", "/img_")
    image = Dir.glob("#{jpeg_home}/#{jpg}.*")[0]
  end
  return image
end # find_image

post_name = ARGV[0]
album_name = ARGV[1]
password = ARGV[2]

fname = find_post(post_name)

ifp = ImagesFromPicasa.new(password)
album_id = ifp.create_album(album_name)

slides = extract_slides(fname)
target_dir = establish_target_dir(post_name)

slides.each do |jpg|
  fname = jpg.split("/").last
  original = find_image(jpg)
  img = "#{target_dir}/#{fname}.jpg"
  unless File.exists?(img)
    cmd = "convert -resize 2000x2000 #{original} #{img}"
    puts "### #{cmd}"
    system cmd
    ifp.send_photo(album_id,img)
  end # unless File.exists?(img)
end # slides.each
