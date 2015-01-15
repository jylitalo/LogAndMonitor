require 'Picasa' # https://github.com/morgoth/picasa

class ImagesFromPicasa
  def initialize(password)
    @client = Picasa::Client.new(user_id: "juha.ylitalo@gmail.com", password: password)
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
    return nil
  end # find_album_id

  def create_album(name)
    album_id = self.find_album_id(name)
    if not album_id.nil?
      puts "### Found existing album #{album_id}"
      return album_id
    end

    album = @client.album.create(title: name, access: "public")
    puts "### Created new album #{album.id}"
    return album.id
  end  # create_album

  def send_photo(album_id,fname)
    puts "### Uploading photo #{fname} to #{album_id}"
    @client.photo.create(album_id, file_path: fname)
  end

  def fetch_links(album)
    resolution="w1280-h800"
    links = {}
    album_id = self.find_album_id(album)
    if album_id.nil?
      puts "### No album id found for #{name}"
      exit 3
    end

    @client.album.show(album_id).entries.each do |photo|
      url = photo.media.thumbnails[0].url
      url.sub!(/\/s[0-9]+\//,"/#{resolution}-no/")
      jpg = url.split("/").last
      # puts "### JPG = >#{jpg}< >#{url}<"
      links[jpg] = url
    end # client.album.show().entries
    return links
  end # fetch_links
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
