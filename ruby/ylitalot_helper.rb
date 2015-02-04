require 'yaml'
require 'Picasa' # https://github.com/morgoth/picasa

class ImagesFromPicasa
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

  def connect
    @client = Picasa::Client.new(user_id: @user_id, password: @password)
  end # connect

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

  def create_album(name)
    unless @album_id.nil?
      puts "### Found existing album #{@album_id}"
      return @album_id
    end

    @album_id = @client.album.create(title: name, access: "public").id
    puts "### Created new album #{@album_id}"
    return @album_id
  end  # create_album

  def _put_photo_into_links(photo)
    resolution="w1280-h800"
    url = photo.media.thumbnails[0].url
    url.sub!(/\/s[0-9]+\//,"/#{resolution}-no/")
    jpg = url.split("/").last
    @links[jpg] = url
  end

  def send_photo(fname)
    count = 0
    puts "### Uploading photo #{fname} to #{@album_id}"
    begin
      photo = @client.photo.create(@album_id, file_path: fname)
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

  def fetch_links
    if @album_id.nil?
      puts "### No album id found for #{name}"
      exit 3
    end

    @client.album.show(@album_id).entries.each do |photo|
      self._put_photo_into_links(photo)
    end # client.album.show().entries
    return @links
  end # fetch_links

  def slide2gslide(line)
    jpg = extract_jpg(line).split("/").last
    suffix = nil
    if @links.has_key?(jpg + ".jpg")
      suffix = ".jpg"
    elsif @links.has_key?(jpg + ".JPG")
      suffix = ".JPG"
    else
      puts "Unable to find G+ image for #{jpg}"
      return line
    end # if

    if line.start_with?("{% slide /images")
      line.sub! "{% slide ", "{% gslide "
      line.sub! " %}", " #{@links[jpg + suffix]} %}"
    end # if
    @links.delete(jpg + suffix)
    return line
  end # slide2gslide

  def print_links
    if @links.empty?
      puts "### All links processed"
    else
      puts "### Following anomalies found:"
      puts @links
    end # if
  end # print_links

end # class ImagesFromPicasa

def find_post(name)
  fnames = Dir.glob("_posts/*[0-9]-#{name}.markdown")
  if fnames.length == 0
    puts "No matching article found (searched for *[0-9]-#{name}.markdown"
    exit 1
  elsif fnames.length > 1
    puts "Found more than one match (searched for *-#{name}.markdown and found #{fnames})"
    exit 2
  end
  puts "### Found #{fnames[0]}"
  return fnames[0]
end # find_post

def find_album_name(post)
  fin = File.open(post)
  fin.each_line do |line|
    if line.start_with?("<!-- G+: ")
      fin.close
      return line.split(" ")[2..-2].join(" ")
    end # if
  end # fin.each_line
  fin.close
end # find_album_name

def extract_jpg(line)
  fields = line.split(" ")
  return fields[2].split("/",3)[2]
end # extract_jpg
