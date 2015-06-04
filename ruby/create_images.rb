require 'yaml'
require 'Picasa' # https://github.com/morgoth/picasa

###
class PicasaInterface
  attr_accessor: links
  ###
  def initialize(album)
    config_file = "#{Dir.home()}/.ylitalot"
    config  = YAML.load_file(config_file)
    @user_id = config['picasa']['username']
    @password = config['picasa']['password']
    @links = {}
    connect
    @album_id = find_album_id album
    if @album_id.nil?
      self.create_album album
    else
      self.fetch_links
    end
  end # initialize

  ###
  def connect
    @client = Picasa::Client.new(user_id: @user_id, authorization_header: "OAuth " + @password)
  end # connect

  ###
  def find_album_id(name)
    @client.album.list.entries.each do |album|
      if album.title == name
        @album_id = album.id
        puts "### Found album id ##{@album_id} for #{name}"
        return @album_id
      end # if album.title ...
    end # client.album.list.entries.each

    return nil
  end # find_album_id

  ###
  def create_album(name)
    unless @album_id.nil?
      puts "### Found existing album #{@album_id}"
      return @album_id
    end #unless

    @album_id = @client.album.create(title: name, access: "public").id
    puts "### Created new album #{@album_id}"
    return @album_id
  end  # create_album

  ###
  def _put_photo_into_links(photo)
    resolution="w1280-h800"
    url = photo.media.thumbnails[0].url
    url.sub!(/\/s[0-9]+\//,"/#{resolution}-no/")
    jpg = url.split("/").last
    @links[jpg] = url
  end

  ###
  def send_photo(fname)
    count = 0
    puts "### Uploading photo #{fname} to #{@album_id}"
    begin
      photo = @client.photo.create(@album_id, file_path: fname)
    rescue Errno::ENOENT
      puts "### Unable to find file #{fname}"
      raise
    rescue SystemCallError
      count += 1
      if count < 3
        connect
        puts "### System call error ... retrying #{count}"
        retry
      else
        puts "### Retries ran out ... exiting"
        raise
      end # if 
    end # begin
    puts "### Upload completed ..." if count > 0
    self._put_photo_into_links(photo)
  end # send_photo

  ###
  def fetch_links
    if @album_id.nil?
      puts "### No album id found for #{name}"
      exit 3
    end # if

    @client.album.show(@album_id).entries.each do |photo|
      self._put_photo_into_links(photo)
    end # client.album.show().entries
    return @links
  end # fetch_links
end # class PicasaInterface

###
class JekyllPost
  attr_accessor: album,name
  ###
  def initialize(name)
    fnames = Dir.glob("_posts/*[0-9]-#{name}.markdown")
    if fnames.length == 0
      puts "No matching article found (searched for *[0-9]-#{name}.markdown"
      exit 1
    elsif fnames.length > 1
      puts "Found more than one match (searched for *-#{name}.markdown and found #{fnames})"
      exit 2
    end
    @name = name
    @fname = fnames[0]
    puts "### Found #{@fname}"

    @album = get_album_name
  end # initialize

  ###
  def get_album_name
    ret = nil
    fin = File.open(@fname)
    fin.each_line do |line|
      if line.start_with?("<!-- G+: ")
        ret = line.split(" ")[2..-2].join(" ")
        break
      end # if
    end # fin.each_line
    fin.close
    return ret
  end # album_name

  ###
  def slides
    ret = []
    f = File.open(@fname)
    f.each_line do |line|
      if line.start_with?("{% slide /images")
        ret += [extract_jpg(line)]
      end # if
    end # f.each_line
    f.close
    return ret
  end # slides

  ###
  def slide2gslide(links)
    new_fname = @fname + ".new"

    fin = File.open(@fname)
    fout = File.open(new_fname,"w")
    fin.each_line do |line|
      if line.start_with?("{% slide /images")
        line = slide2gslide_line(line,links)
      elsif line.start_with?("{% gslide /images")
        slide2gslide_line(line,links)
      end # if
      fout.write(line) unless line.start_with?("<!-- G+: ")
    end # fin.each_line
    fout.write("\n<!-- G+: #{@album} -->\n")
    fout.close
    fin.close

    File.unlink(@fname)
    File.rename(new_fname,@fname)

    if links.empty?
      puts "### All links processed"
    else
      puts "### Following anomalies found:"
      puts links
    end # if
  end # slide2gslide

  ###
  def slide2gslide_line(line,links)
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
  end # slide2gslide_line

  ###
  def extract_jpg(line)
    fields = line.split(" ")
    return fields[2].split("/",3)[2]
  end # extract_jpg
end # JekyllPost

###
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

###
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

###
# main
###
post = Post.new ARGV[0]
puts "### Album from post: #{post.album}"
pi = PicasaInterface.new post.album

###
# Find slides in a post, create images and upload them.
###
target_dir = establish_target_dir(post.name)

post.slides.each do |jpg|
  fname = jpg.split("/").last
  original = find_image(jpg)
  img = "#{target_dir}/#{fname}.jpg"
  unless File.exists?(img)
    cmd = "convert -resize 2000x2000 #{original} #{img}"
    puts "### #{cmd}"
    system cmd
  end # unless File.exists?(img)
  pi.send_photo(img)
  File.unlink(img)
end # slides.each


###
# Fix links in post
###
post.slide2gslide(pi.links)
Dir.rmdir(target_dir)
