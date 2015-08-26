require "signet/oauth_2"
require "signet/oauth_2/client"
require 'yaml'
require 'Picasa' # https://github.com/morgoth/picasa

###
class PicasaInterface
  attr_accessor :links, :delete
  ###
  def initialize(album)
    config_file = "#{Dir.home()}/.ylitalot"
    config  = YAML.load_file(config_file)
    @user_id = config['picasa']['username']
    @client_id = config['picasa']['client_id']
    @client_secret = config['picasa']['client_secret']
    @refresh_token = config['picasa']['refresh_token']
    @delete = config['picasa']['delete'].to_s
    puts "### delete in config: #{@delete}"
    @links = {}
    connect
    if album.nil?
      a_list = @client.album.list.entries
      a_list.map! {|a| a.title.to_s }
      a_list.sort!
      puts "### Album list: "
      a_list.each do |a|
        puts a
      end
      puts "### Doing exit ..."
      exit 4
    end
    @album_id = find_album_id album
    if @album_id.nil?
      self.create_album album
    else
      self.fetch_links
    end
  end # PicasaInterface.initialize

  ###
  def connect
    oauth2_client = Signet::OAuth2::Client.new(
      authorization_uri: "https://accounts.google.com/o/oauth2/auth",
      token_credential_uri: "https://accounts.google.com/o/oauth2/token",
      client_id: @client_id,
      client_secret: @client_secret,
      redirect_uri: "urn:ietf:wg:oauth:2.0:oob",
      scope: "https://picasaweb.google.com/data/",
      expiry: 3600,
      refresh_token: @refresh_token
    )
    oauth2_client.refresh!
    @client = Picasa::Client.new(user_id: @user_id, authorization_header: "Bearer " + oauth2_client.access_token)
  end # PicasaInterface.connect

  ###
  def find_album_id(name)
    @client.album.list.entries.each do |album|
      if album.title == name
        @album_id = album.id
        puts "### Found album #{album.links[1].href} for #{name}"
        return @album_id
      end # if album.title ...
    end # client.album.list.entries.each

    return nil
  end # PicasaInterface.find_album_id

  ###
  def create_album(name)
    unless @album_id.nil?
      puts "### Found existing album #{@album_id}"
      return @album_id
    end #unless

    @album_id = @client.album.create(title: name, access: "public").id
    puts "### Created new album #{@album_id}"
    return @album_id
  end  # PicasaInterface.create_album

  ###
  def _put_photo_into_links(photo)
    resolution="w1280-h800"
    # puts photo.media.thumbnails[0].url
    url = photo.media.thumbnails[0].url
    url.sub!(/\/s[0-9]+\//,"/#{resolution}-no/")
    jpg = url.split("/").last
    if @links.has_key?(jpg)
      puts "!!! #{jpg} had duplicate in album"
      delete_photo(jpg)
    end # if duplicate found
    @links[jpg] = [url,photo.id]
  end # PicasaInterface._put_photo_into_links

  ###
  def send_photo(fname)
    count = 0
    # puts "### Uploading photo #{fname} to #{@album_id}"
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
  end # PicasaInterface.send_photo

  ###
  def delete_photo(fname)
    puts "!!! Deleting #{fname}"
    @client.photo.destroy(@album_id, links[fname][1])
    links.delete(fname)
  end # PicasaInterface.delete_photo

  ###
  def fetch_links
    if @album_id.nil?
      puts "### No album id found for #{name}"
      exit 3
    end # if

    @client.album.show(@album_id).entries.each do |photo|
      self._put_photo_into_links(photo)
    end # client.album.show().entries
    puts "--- found #{@links.length} links"
    return @links
  end # PicasaInterface.fetch_links

  def purge
    if @delete == "true"
      @links.each do |key,p|
        delete_photo(key)
      end # .each
    elsif links.empty?
      puts "### All links processed"
    else
      puts "### Following anomalies found:"
      puts links
    end # if
  end # PicasaInterface.purge
end # class PicasaInterface

###
class JekyllPost
  attr_accessor :album,:name,:uploaded
  ###
  def initialize(name)
    fnames = Dir.glob("_posts/*[0-9]-#{name}.markdown")
    if fnames.length == 0
      puts "No matching article found (searched for *[0-9]-#{name}.markdown"
      exit 1
    elsif fnames.length > 1
      puts "Found more than one match (searched for *-#{name}.markdown and found #{fnames})"
      exit 2
    end # if
    @name = name
    @fname = fnames[0]
    puts "### Found #{@fname}"

    @album, @uploaded = get_album_info
  end # JekyllPost.initialize

  ###
  def get_album_info
    album_name = nil
    upload_time = 1440512694
    fin = File.open(@fname)
    fin.each_line do |line|
      if /^<!-- G\+\([0-9]+\): /.match(line)
        upload_time = /^<!-- G\+\([0-9]+\): /.match(line).to_s[8..-2].to_i
      end
      if /^<!-- G\+[\(0-9\)]*: /.match(line)
        album_name = line.split(" ")[2..-2].join(" ")
        break
      end # if
    end # fin.each_line
    fin.close
    return album_name,upload_time
  end # JekyllPost.album_name

  ###
  def slides
    ret = []
    f = File.open(@fname)
    f.each_line do |line|
      if line.start_with?("{% slide /images") or line.start_with?("{% gslide /images")
        ret += [extract_jpg(line)]
      end # if
    end # f.each_line
    f.close
    puts "--- found #{ret.length} slides"
    return ret
  end # JekyllPost.slides

  ###
  def slide2gslide(links)
    new_fname = @fname + ".new"
    puts "--- slide2gslide on #{@fname}"
    fin = File.open(@fname)
    fout = File.open(new_fname,"w")
    fin.each_line do |line|
      if line.start_with?("{% slide /images") or line.start_with?("{% gslide /images")
        line = slide2gslide_line(line,links)
      end # if
      fout.write(line) unless line.start_with?("<!-- G+")
    end # fin.each_line
    fout.write("<!-- G+(#{Time.now().to_i}): #{@album} -->\n")
    fout.close
    fin.close

    File.unlink(@fname)
    File.rename(new_fname,@fname)
  end # JekyllPost.slide2gslide

  ###
  def slide2gslide_line(line,links)
    jpg = extract_jpg(line).split("/").last + ".jpg"
    if not links.has_key?(jpg)
      puts "Unable to find G+ image for #{jpg}"
      return line
    end # if
    # puts "--- matching #{jpg} into line"
    key = links[jpg][0]
    if line.start_with?("{% slide /images")
      line.sub! "{% slide ", "{% gslide "
      line.sub! " %}", " #{key} %}"
    elsif line.start_with?("{% gslide /images")
      line.sub! /https:[^ ]+/, "#{key}"
    end # if
    links.delete(jpg)
    # puts "--- #{links.length} still left"
    return line
  end # JekyllPost.slide2gslide_line

  ###
  def extract_jpg(line)
    fields = line.split(" ")
    return fields[2].split("/",3)[2]
  end # JekyllPost.extract_jpg
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
post = JekyllPost.new ARGV[0]
puts "### Album from post: #{post.album}"
puts "### Uploaded at: #{post.uploaded}"
pi = PicasaInterface.new post.album
if ARGV.length > 1
  pi.delete = ARGV[1]
  puts "### delete set to #{pi.delete}"
end
###
# Find slides in a post, create images and upload them.
###
target_dir = establish_target_dir(post.name)

post.slides.each do |jpg|
  fname = jpg.split("/").last + ".jpg"
  original = find_image(jpg)
  mtime = File.new(original).mtime.to_i
  if pi.links.has_key?(fname)
    # puts "--- mtime #{mtime} vs. #{post.uploaded} on #{fname}"
    if mtime > post.uploaded
      pi.delete_photo(fname)
    end # if picasa image should be replaced
  end
  if not pi.links.has_key?(fname)
    img = "#{target_dir}/#{fname}"
    unless File.exists?(img)
      cmd = "convert -resize 2000x2000 #{original} #{img}"
      puts "### #{cmd}"
      system cmd
    end # unless File.exists?(img)
    pi.send_photo(img)
    File.unlink(img)
  end # if
end # slides.each


###
# Fix links in post
###
post.slide2gslide(pi.links)
pi.purge
Dir.rmdir(target_dir)
